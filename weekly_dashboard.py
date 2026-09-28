from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from classification import classify_model


SCHEMA_VERSION = 1
SNAPSHOT_RE = re.compile(r"models_(\d{8})\.csv\.gz$")
REQUIRED_FIELDS = {"snapshot_date", "id", "downloads_all_time", "downloads_30d", "likes", "trending_score", "pipeline_tag", "library_name", "tags"}
EXACT_LIMIT, WATCH_LIMIT = 450, 50


@dataclass(frozen=True)
class SnapshotRef:
    snapshot_date: date
    data_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class Snapshot:
    snapshot_date: date
    captured_at_utc: str
    manifest: dict[str, Any]
    rows: dict[str, dict[str, str]]


def as_int(value: Any) -> int | None:
    try:
        return None if value in (None, "") else int(float(value))
    except (TypeError, ValueError):
        return None


def as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def parse_tags(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
        return [str(item) for item in parsed] if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return [part.strip() for part in (value or "").split("|") if part.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def local_snapshot_refs(directory: Path) -> dict[date, SnapshotRef]:
    refs: dict[date, SnapshotRef] = {}
    for data_path in directory.glob("models_*.csv.gz"):
        match = SNAPSHOT_RE.match(data_path.name)
        if not match:
            continue
        manifest_path = directory / f"manifest_{match.group(1)}.json"
        if manifest_path.exists():
            refs[datetime.strptime(match.group(1), "%Y%m%d").date()] = SnapshotRef(
                datetime.strptime(match.group(1), "%Y%m%d").date(), data_path, manifest_path
            )
    return refs


def download_bytes(url: str, token: str | None = None) -> bytes:
    headers = {"Accept": "application/octet-stream", "User-Agent": "hf-trend-snapshots-dashboard/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to download {url}: {exc}") from exc


def fetch_remote_refs(repo: str, cache_dir: Path, token: str | None) -> dict[date, SnapshotRef]:
    api_url = f"https://api.github.com/repos/{repo}/releases?per_page=100"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "hf-trend-snapshots-dashboard/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            releases = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to list GitHub releases for {repo}: {exc}") from exc
    if not isinstance(releases, list):
        raise RuntimeError(f"GitHub releases API returned an invalid payload for {repo}")

    candidates: dict[date, tuple[str, Any, Any]] = {}
    for release in releases:
        assets = {str(asset.get("name", "")): asset for asset in release.get("assets", [])}
        for name, asset in assets.items():
            match = SNAPSHOT_RE.match(name)
            if not match:
                continue
            stamp = match.group(1)
            manifest_asset = assets.get(f"manifest_{stamp}.json")
            if not manifest_asset:
                continue
            snapshot_day = datetime.strptime(stamp, "%Y%m%d").date()
            candidates[snapshot_day] = (stamp, asset, manifest_asset)

    refs: dict[date, SnapshotRef] = {}
    # The current local snapshot supersedes a same-day release, so three remote
    # candidates are enough to supply the two preceding periods without
    # downloading the entire 52-week release archive on every workflow run.
    for snapshot_day in sorted(candidates, reverse=True)[:3]:
        stamp, asset, manifest_asset = candidates[snapshot_day]
        data_path, manifest_path = cache_dir / f"models_{stamp}.csv.gz", cache_dir / f"manifest_{stamp}.json"
        cache_dir.mkdir(parents=True, exist_ok=True)
        if not data_path.exists():
            data_path.write_bytes(download_bytes(str(asset["url"]), token))
        if not manifest_path.exists():
            manifest_path.write_bytes(download_bytes(str(manifest_asset["url"]), token))
        refs[snapshot_day] = SnapshotRef(snapshot_day, data_path, manifest_path)
    return refs


def load_snapshot(ref: SnapshotRef) -> Snapshot:
    manifest = json.loads(ref.manifest_path.read_text(encoding="utf-8"))
    expected = str(manifest.get("sha256", "")).lower()
    if not expected or sha256_file(ref.data_path) != expected:
        raise RuntimeError(f"Manifest checksum failed: {ref.data_path.name}")
    rows: dict[str, dict[str, str]] = {}
    with gzip.open(ref.data_path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(f"Missing fields in {ref.data_path.name}: {sorted(missing)}")
        for row in reader:
            model_id = (row.get("id") or "").strip()
            if not model_id or model_id in rows:
                raise RuntimeError(f"Invalid or duplicate model id in {ref.data_path.name}: {model_id!r}")
            if row.get("snapshot_date") != ref.snapshot_date.isoformat():
                raise RuntimeError(f"Wrong snapshot_date in {ref.data_path.name}: {model_id}")
            rows[model_id] = row
    if not rows or int(manifest.get("row_count", -1)) != len(rows):
        raise RuntimeError(f"Row count mismatch or empty snapshot: {ref.data_path.name}")
    return Snapshot(ref.snapshot_date, str(manifest.get("captured_at_utc", "")), manifest, rows)


def _exact_note(row: dict[str, Any]) -> str:
    suffix = "；已按原始间隔折算为7日等效值" if row["current_period_days"] != 7 or row["previous_period_days"] != 7 else ""
    return (f"本期({row['current_period_start']}至{row['current_period_end']}){row['downloads_this_period']:,}次，"
            f"上期({row['previous_period_start']}至{row['previous_period_end']}){row['downloads_last_period']:,}次，"
            f"净增加{row['download_acceleration']:,}次{suffix}。")


def compute_weekly(latest: Snapshot, previous: Snapshot, earlier: Snapshot) -> dict[str, Any]:
    current_days = (latest.snapshot_date - previous.snapshot_date).days
    previous_days = (previous.snapshot_date - earlier.snapshot_date).days
    if not 0 < current_days <= 21 or not 0 < previous_days <= 21:
        raise ValueError(f"Snapshot gap is invalid: {previous_days} days then {current_days} days")
    exact_rows: list[dict[str, Any]] = []
    watch_rows: list[dict[str, Any]] = []
    invalid_count = 0
    for model_id, latest_row in latest.rows.items():
        category = classify_model(model_id, latest_row.get("pipeline_tag"), latest_row.get("library_name"), parse_tags(latest_row.get("tags")))
        common = {
            "id": model_id, "model_url": "https://huggingface.co/" + urllib.parse.quote(model_id, safe="/"),
            "likes": as_int(latest_row.get("likes")) or 0, "task_type": category.task_type,
            "remark": category.remark, "downloads_30d": as_int(latest_row.get("downloads_30d")) or 0,
            "trending_score": as_float(latest_row.get("trending_score")),
        }
        tag_text = ", ".join(parse_tags(latest_row.get("tags"))[:6])
        common["use_case_zh"] = f"主要用于{category.task_type}；" + (f"标签：{tag_text}" if tag_text else "用途以模型卡片为准，建议打开链接查看 README。")
        previous_row, earlier_row = previous.rows.get(model_id), earlier.rows.get(model_id)
        if not previous_row or not earlier_row:
            watch_rows.append({**common, "status": "watch", "rank": None,
                "download_note": f"新上榜观察：历史快照不足；官方近30日下载{common['downloads_30d']:,}次，HF趋势分{common['trending_score']:g}。"})
            continue
        values = [as_int(row.get("downloads_all_time")) for row in (latest_row, previous_row, earlier_row)]
        if any(value is None for value in values) or values[0] < values[1] or values[1] < values[2]:
            invalid_count += 1
            continue
        current_week = round((values[0] - values[1]) * 7 / current_days)
        previous_week = round((values[1] - values[2]) * 7 / previous_days)
        item = {**common, "status": "exact", "downloads_this_period": current_week,
            "downloads_last_period": previous_week, "download_acceleration": current_week - previous_week,
            "current_period_start": previous.snapshot_date.isoformat(), "current_period_end": latest.snapshot_date.isoformat(),
            "previous_period_start": earlier.snapshot_date.isoformat(), "previous_period_end": previous.snapshot_date.isoformat(),
            "current_period_days": current_days, "previous_period_days": previous_days}
        item["download_note"] = _exact_note(item)
        exact_rows.append(item)
    exact_rows.sort(key=lambda row: (row["download_acceleration"], row["downloads_this_period"], row["likes"]), reverse=True)
    watch_rows.sort(key=lambda row: (row["trending_score"], row["downloads_30d"], row["likes"]), reverse=True)
    exact_rows, watch_rows = exact_rows[:EXACT_LIMIT], watch_rows[:WATCH_LIMIT]
    for rank, row in enumerate(exact_rows, start=1):
        row["rank"] = rank
    return {"exact_count": len(exact_rows), "watch_count": len(watch_rows), "invalid_count": invalid_count, "rows": exact_rows + watch_rows}


def build_payload(snapshots: list[Snapshot]) -> dict[str, Any]:
    latest, previous, earlier = snapshots
    weekly = compute_weekly(latest, previous, earlier)
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": "hugging_face_weekly",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "latest_captured_at_utc": latest.captured_at_utc,
        "source": "Hugging Face Hub official API",
        "snapshot_dates": [earlier.snapshot_date.isoformat(), previous.snapshot_date.isoformat(), latest.snapshot_date.isoformat()],
        "latest_snapshot_sha256": latest.manifest.get("sha256"),
        **weekly,
    }


def validate_payload(payload: dict[str, Any]) -> None:
    required = {"schema_version", "dataset", "generated_at_utc", "latest_captured_at_utc", "snapshot_dates", "exact_count", "watch_count", "invalid_count", "rows"}
    if required - set(payload) or payload.get("dataset") != "hugging_face_weekly" or len(payload.get("snapshot_dates", [])) != 3:
        raise RuntimeError("Dashboard payload contract is invalid")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) > EXACT_LIMIT + WATCH_LIMIT:
        raise RuntimeError("Dashboard payload has an invalid row count")
    if sum(1 for row in rows if row.get("status") == "exact") != payload["exact_count"] or sum(1 for row in rows if row.get("status") == "watch") != payload["watch_count"]:
        raise RuntimeError("Dashboard payload counts do not match rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public Hugging Face weekly dashboard payload.")
    parser.add_argument("--current-dir", type=Path, required=True)
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--cache-dir", type=Path, default=Path("history"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    refs = fetch_remote_refs(args.repo, args.cache_dir, os.environ.get("GH_TOKEN"))
    refs.update(local_snapshot_refs(args.current_dir))
    selected = [refs[item] for item in sorted(refs, reverse=True)[:3]]
    if len(selected) < 3:
        print(f"Only {len(refs)} valid snapshots are available; dashboard waits for three.", file=sys.stderr)
        raise SystemExit(3)
    payload = build_payload([load_snapshot(ref) for ref in selected])
    validate_payload(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} with {len(payload['rows'])} rows")


if __name__ == "__main__":
    main()

"""Convert a GitHub snapshot into the stable public dashboard envelope."""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in snapshot.get("rows", []):
        weekly = item.get("stars_this_week")
        rows.append({
            "rank": item.get("rank"), "full_name": item.get("full_name"), "url": item.get("url"),
            "stars": item.get("stars"), "stars_this_week": weekly, "forks": item.get("forks"),
            "language": item.get("language") or "", "topics": item.get("topics") or [],
            "domain": item.get("domain") or "非AI/待复核", "description_raw": item.get("description_raw") or item.get("page_description") or "",
            "use_case_zh": item.get("use_case_zh") or item.get("description_raw") or item.get("readme_excerpt") or "暂无项目简介，建议查看 README。",
            "use_case_source": item.get("use_case_source") or "GitHub description", "readme_excerpt": item.get("readme_excerpt") or "",
            "source_type": item.get("source_type") or "trending", "latest_release": item.get("latest_release"),
        })
    rows.sort(key=lambda row: (row["stars_this_week"] is not None, row["stars_this_week"] or -1, -(row["rank"] or 999)), reverse=True)
    for rank, row in enumerate(rows, 1):
        row["weekly_rank"] = rank
    return {"schema_version": 1, "dataset": "github_trending_weekly", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "snapshot_date": snapshot.get("snapshot_date"), "captured_at_utc": snapshot.get("captured_at_utc"), "source": snapshot.get("source"), "count": len(rows), "rows": rows}


def validate(payload: dict[str, Any]) -> None:
    if payload.get("dataset") not in ("github_trending_weekly","github_ai_ecosystem") or not isinstance(payload.get("rows"), list):
        raise RuntimeError("GitHub dashboard payload contract is invalid")
    if payload.get("count") != len(payload["rows"]):
        raise RuntimeError("GitHub dashboard count does not match rows")


def restore_latest(repo: str, output: Path, token: str | None) -> Path:
    """Restore the last successful collector asset when this week's scrape fails."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-industry-research-dashboard/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases?per_page=100", headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        releases = json.loads(response.read().decode("utf-8"))
    candidates = []
    for release in releases:
        if str(release.get("tag_name", "")).startswith("github-snapshot-"):
            for asset in release.get("assets", []):
                if str(asset.get("name", "")).startswith("github_snapshot_") and asset.get("browser_download_url"):
                    candidates.append((str(release.get("tag_name")), asset["browser_download_url"]))
    if not candidates:
        raise RuntimeError("No previous GitHub snapshot release is available")
    candidates.sort(reverse=True)
    download = urllib.request.Request(candidates[0][1], headers={"Accept": "application/octet-stream", "User-Agent": headers["User-Agent"], **({"Authorization": headers["Authorization"]} if token else {})})
    with urllib.request.urlopen(download, timeout=120) as response:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.read())
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--repo")
    parser.add_argument("--restore-to", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    input_path = args.input
    if input_path is None or not input_path.exists():
        if not args.repo or not args.restore_to:
            raise SystemExit("provide --input, or --repo and --restore-to for fallback")
        try:
            input_path = restore_latest(args.repo, args.restore_to, os.environ.get("GH_TOKEN"))
        except Exception:
            if not args.allow_empty:
                raise
            input_path = args.restore_to
            input_path.parent.mkdir(parents=True, exist_ok=True)
            input_path.write_text(json.dumps({"dataset": "github_trending_weekly", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "snapshot_date": None, "source": "GitHub Trending", "rows": []}), encoding="utf-8")
    payload = build_payload(json.loads(input_path.read_text(encoding="utf-8")))
    validate(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

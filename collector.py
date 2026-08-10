from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi


SCHEMA_VERSION = 2
FIELDS = [
    "captured_at_utc",
    "snapshot_date",
    "id",
    "author",
    "downloads_all_time",
    "downloads_30d",
    "likes",
    "trending_score",
    "pipeline_tag",
    "library_name",
    "tags",
    "created_at",
    "last_modified",
    "source_lists",
]
EXPAND = [
    "author",
    "downloads",
    "downloadsAllTime",
    "likes",
    "trendingScore",
    "pipeline_tag",
    "library_name",
    "tags",
    "createdAt",
    "lastModified",
]
QUERIES = {
    "downloads": ("downloads", 10_000),
    "trending": ("trending_score", 5_000),
    "likes": ("likes", 5_000),
    "created": ("created_at", 5_000),
    "modified": ("last_modified", 5_000),
}
MIN_UNIQUE_MODELS = 10_000


def iso(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def int_value(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def fetch_list(api: HfApi, label: str, sort: str, limit: int, retries: int = 5):
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            rows = list(api.list_models(sort=sort, limit=limit, expand=EXPAND))
            if len(rows) != limit:
                raise RuntimeError(f"{label} returned {len(rows):,} rows; expected {limit:,}")
            return rows
        except Exception as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(min(60, 2**attempt))
    raise RuntimeError(f"Hugging Face query '{label}' failed after {retries} attempts: {last_error}")


def model_record(model: Any, captured_at: str, snapshot_date: str, source: str) -> dict[str, Any]:
    model_id = str(getattr(model, "id", "") or "").strip()
    return {
        "captured_at_utc": captured_at,
        "snapshot_date": snapshot_date,
        "id": model_id,
        "author": str(getattr(model, "author", "") or ""),
        "downloads_all_time": int_value(getattr(model, "downloads_all_time", 0)),
        "downloads_30d": int_value(getattr(model, "downloads", 0)),
        "likes": int_value(getattr(model, "likes", 0)),
        "trending_score": getattr(model, "trending_score", 0) or 0,
        "pipeline_tag": str(getattr(model, "pipeline_tag", "") or ""),
        "library_name": str(getattr(model, "library_name", "") or ""),
        "tags": json.dumps(list(getattr(model, "tags", None) or []), ensure_ascii=False, separators=(",", ":")),
        "created_at": iso(getattr(model, "created_at", None)),
        "last_modified": iso(getattr(model, "last_modified", None)),
        "source_lists": source,
    }


def merge_record(existing: dict[str, Any], incoming: dict[str, Any], source: str) -> None:
    sources = set(str(existing.get("source_lists", "")).split("|"))
    sources.add(source)
    existing["source_lists"] = "|".join(sorted(item for item in sources if item))
    for key in FIELDS:
        if key == "source_lists":
            continue
        if existing.get(key) in (None, "", 0, "[]") and incoming.get(key) not in (None, "", 0, "[]"):
            existing[key] = incoming[key]


def write_gzip_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                writer = csv.DictWriter(text, fieldnames=FIELDS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_rows(rows: list[dict[str, Any]]) -> None:
    if len(rows) < MIN_UNIQUE_MODELS:
        raise RuntimeError(f"Only {len(rows):,} unique models collected; minimum is {MIN_UNIQUE_MODELS:,}")
    ids = [row["id"] for row in rows]
    if any(not model_id for model_id in ids):
        raise RuntimeError("Blank model id found")
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate model id found")
    invalid = [row["id"] for row in rows if int_value(row["downloads_all_time"]) < 0]
    if invalid:
        raise RuntimeError(f"Negative downloads_all_time found for {invalid[:5]}")


def collect(output_dir: Path, snapshot_day: date | None = None) -> tuple[Path, Path]:
    now = datetime.now(timezone.utc)
    snapshot_day = snapshot_day or now.date()
    snapshot_date = snapshot_day.isoformat()
    captured_at = now.isoformat()
    api = HfApi(token=os.environ.get("HF_TOKEN") or False)

    merged: dict[str, dict[str, Any]] = {}
    query_counts: dict[str, int] = {}
    for label, (sort, limit) in QUERIES.items():
        print(f"Collecting {label}: sort={sort}, limit={limit:,}", flush=True)
        models = fetch_list(api, label, sort, limit)
        query_counts[label] = len(models)
        for model in models:
            incoming = model_record(model, captured_at, snapshot_date, label)
            model_id = incoming["id"]
            if not model_id:
                raise RuntimeError(f"Blank model id returned by query {label}")
            if model_id in merged:
                merge_record(merged[model_id], incoming, label)
            else:
                merged[model_id] = incoming

    rows = [merged[model_id] for model_id in sorted(merged)]
    validate_rows(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = snapshot_day.strftime("%Y%m%d")
    data_path = output_dir / f"models_{stamp}.csv.gz"
    manifest_path = output_dir / f"manifest_{stamp}.json"
    write_gzip_csv(data_path, rows)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": snapshot_date,
        "captured_at_utc": captured_at,
        "row_count": len(rows),
        "sha256": sha256_file(data_path),
        "query_counts": query_counts,
        "query_limits": {label: limit for label, (_, limit) in QUERIES.items()},
        "fields": FIELDS,
        "source": "Hugging Face Hub official API",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "release.env").write_text(
        f"stamp={stamp}\ndata_file={data_path.name}\nmanifest_file={manifest_path.name}\n",
        encoding="utf-8",
    )
    print(f"Collected {len(rows):,} unique models", flush=True)
    return data_path, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect compact Hugging Face model popularity snapshots.")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--snapshot-date", type=date.fromisoformat)
    args = parser.parse_args()
    data_path, manifest_path = collect(args.output_dir, args.snapshot_date)
    print(data_path)
    print(manifest_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


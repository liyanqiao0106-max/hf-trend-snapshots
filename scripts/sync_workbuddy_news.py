"""Sync the local WorkBuddy AI news board into the GitHub Pages site.

The WorkBuddy project remains the authoring source. This bridge copies its
self-contained board and dated reports into a stable Pages subdirectory so a
future WorkBuddy run only needs to invoke this script before publishing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/Users/liyanqiao/Documents/WorkBuddy/AI每日新闻/ai-news-board")
DESTINATION = PROJECT_ROOT / "site" / "ai-news-daily"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sync(source: Path, destination: Path) -> dict:
    source = source.expanduser().resolve()
    if not (source / "index.html").is_file():
        raise SystemExit(f"WorkBuddy board index not found: {source / 'index.html'}")
    source_reports = sorted((source / "reports").glob("*.html"))
    if not source_reports:
        raise SystemExit(f"No WorkBuddy report HTML files found: {source / 'reports'}")

    destination.mkdir(parents=True, exist_ok=True)
    report_destination = destination / "reports"
    report_destination.mkdir(exist_ok=True)
    shutil.copy2(source / "index.html", destination / "index.html")
    for report in source_reports:
        shutil.copy2(report, report_destination / report.name)

    files = [destination / "index.html", *sorted(report_destination.glob("*.html"))]
    manifest = {
        "schema_version": 1,
        "dataset": "workbuddy_ai_news_board",
        "source": str(source),
        "synced_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "board": "index.html",
        "reports": [
            {"file": f"reports/{path.name}", "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in files[1:]
        ],
        "report_count": len(files) - 1,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync WorkBuddy AI news HTML into GitHub Pages.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    manifest = sync(args.source, DESTINATION)
    print(f"Synced {manifest['report_count']} reports to {DESTINATION}")


if __name__ == "__main__":
    main()

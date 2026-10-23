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
import re
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


def load_manifest(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def prepare_board(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    html = re.sub(r"\n?\s*<div class=\"notice\">.*?</div>\s*", "\n", html, count=1, flags=re.DOTALL)
    if '<link rel="stylesheet" href="navigation.css">' not in html:
        html = html.replace("</head>", '<link rel="stylesheet" href="navigation.css">\n</head>', 1)
    return_link = '  <a class="return-link" href="../index.html">← 返回总览</a>'
    if return_link not in html:
        html = html.replace('<div class="wrap">', f'<div class="wrap">\n{return_link}', 1)
    path.write_text(html, encoding="utf-8")


def prepare_report(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    if '<link rel="stylesheet" href="../navigation.css">' not in html:
        html = html.replace("</head>", '<link rel="stylesheet" href="../navigation.css">\n</head>', 1)
    return_link = '<a class="return-link" href="../index.html">← 返回 AI 新闻日报</a>'
    if return_link not in html:
        html = html.replace('<div class="wrap">', f'<div class="wrap">\n{return_link}', 1)
    path.write_text(html, encoding="utf-8")


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
    prepare_board(destination / "index.html")
    for report in source_reports:
        destination_report = report_destination / report.name
        shutil.copy2(report, destination_report)
        prepare_report(destination_report)

    files = [destination / "index.html", *sorted(report_destination.glob("*.html"))]
    manifest_path = destination / "manifest.json"
    previous_manifest = load_manifest(manifest_path)
    reports = [
        {"file": f"reports/{path.name}", "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in files[1:]
    ]
    board_sha256 = sha256(files[0])
    content_is_unchanged = (
        previous_manifest.get("source") == str(source)
        and previous_manifest.get("board") == "index.html"
        and previous_manifest.get("board_sha256") == board_sha256
        and previous_manifest.get("reports") == reports
    )
    manifest = {
        "schema_version": 1,
        "dataset": "workbuddy_ai_news_board",
        "source": str(source),
        "synced_at_utc": (
            previous_manifest["synced_at_utc"]
            if content_is_unchanged and previous_manifest.get("synced_at_utc")
            else dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "board": "index.html",
        "board_sha256": board_sha256,
        "reports": reports,
        "report_count": len(files) - 1,
    }
    manifest_path.write_text(
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

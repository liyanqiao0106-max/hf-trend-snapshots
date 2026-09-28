"""Collect a public GitHub Trending snapshot.

This module deliberately has no Excel or dashboard code.  It produces one
small, validated JSON snapshot that can be archived as a Release asset and
consumed by any later presentation layer.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
TRENDING = "https://github.com/trending"
SCHEMA_VERSION = 1


def request_text(url: str, token: str | None = None) -> str:
    headers = {"User-Agent": "ai-industry-research-dashboard/1.0", "Accept-Language": "en-US,en;q=0.9"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def request_json(url: str, token: str | None = None) -> Any:
    headers = {"User-Agent": "ai-industry-research-dashboard/1.0", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def clean(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def integer(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r"[^0-9]", "", html.unescape(value))
    return int(digits) if digits else None


def match(pattern: str, text: str) -> str:
    found = re.search(pattern, text, flags=re.I | re.S)
    return found.group(1).strip() if found else ""


def parse_trending(page: str, source_url: str, captured_at: str) -> list[dict[str, Any]]:
    blocks = re.findall(r'<article\b[^>]*class="[^\"]*\bBox-row\b[^\"]*"[^>]*>(.*?)</article>', page, flags=re.I | re.S)
    rows: list[dict[str, Any]] = []
    for rank, block in enumerate(blocks, 1):
        heading = match(r"(<h2\b.*?</h2>)", block)
        href = match(r'href="/([^"#?]+/[^"#?]+)"', heading or block)
        if not href or href.count("/") != 1:
            continue
        owner, repo = href.split("/", 1)
        path = f"/{owner}/{repo}"
        plain = clean(block)
        rows.append({
            "rank": rank,
            "full_name": f"{owner}/{repo}",
            "url": f"https://github.com/{owner}/{repo}",
            "source_url": source_url,
            "stars_this_week": integer(match(r"(\d[\d,]*)\s+stars?\s+this\s+week", plain)),
            "page_stars": integer(clean(match(rf'<a\b[^>]*href="{re.escape(path)}/stargazers"[^>]*>(.*?)</a>', block))),
            "page_description": clean(match(r"(<p\b.*?</p>)", block)),
            "language": clean(match(r'<span\b[^>]*itemprop="programmingLanguage"[^>]*>(.*?)</span>', block)),
            "captured_at_utc": captured_at,
        })
    if not rows:
        raise RuntimeError("No repositories parsed from GitHub Trending; page layout may have changed")
    return rows


def normalize_readme(text: str, limit: int = 1800) -> str:
    text = re.sub(r"```.*?```|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\)", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>|#+\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def enrich(row: dict[str, Any], token: str | None, include_readme: bool) -> None:
    owner, repo = row["full_name"].split("/", 1)
    status: list[str] = []
    try:
        data = request_json(f"{API}/repos/{owner}/{repo}", token)
        row.update({
            "stars": data.get("stargazers_count", row.get("page_stars")),
            "forks": data.get("forks_count"),
            "language": data.get("language") or row.get("language") or "",
            "description_raw": data.get("description") or row.get("page_description") or "",
            "topics": list(data.get("topics") or []),
            "license": (data.get("license") or {}).get("spdx_id") or "",
            "created_at": data.get("created_at") or "",
            "pushed_at": data.get("pushed_at") or "",
            "open_issues": data.get("open_issues_count"),
            "source_updated_at": data.get("updated_at") or "",
        })
        status.append("repo_api_ok")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        row["description_raw"] = row.get("page_description") or ""
        status.append(f"repo_api_failed:{type(exc).__name__}")
    if include_readme:
        try:
            data = request_json(f"{API}/repos/{owner}/{repo}/readme", token)
            content = data.get("content") or ""
            row["readme_excerpt"] = normalize_readme(base64.b64decode(content).decode("utf-8", errors="replace")) if content else ""
            status.append("readme_ok")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, ValueError):
            row["readme_excerpt"] = ""
            status.append("readme_unavailable")
    row["api_status"] = ";".join(status)
    row["use_case_zh"] = row.get("description_raw") or row.get("readme_excerpt") or "暂无项目简介，建议查看 README。"
    row["use_case_source"] = "GitHub description" if row.get("description_raw") else "README excerpt"


def collect(output: Path, *, date_value: str | None = None, token: str | None = None, limit: int | None = None, no_readme: bool = False) -> Path:
    captured = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    day = date_value or dt.datetime.now(dt.timezone.utc).date().isoformat()
    source_url = f"{TRENDING}?since=weekly"
    rows = parse_trending(request_text(source_url), source_url, captured)
    if limit:
        rows = rows[:limit]
    for row in rows:
        enrich(row, token, not no_readme)
        row["date"] = day
        row["domain"] = classify(row)
        row["use_case_zh"] = make_use_case(row)
    payload = {"schema_version": SCHEMA_VERSION, "dataset": "github_trending_weekly", "generated_at_utc": captured, "captured_at_utc": captured, "snapshot_date": day, "source": "GitHub Trending page + official REST API", "rows": rows}
    validate(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def classify(row: dict[str, Any]) -> str:
    text = " ".join([str(row.get("full_name", "")), str(row.get("description_raw", "")), str(row.get("language", "")), " ".join(row.get("topics", [])), str(row.get("readme_excerpt", ""))]).lower()
    rules = [("MCP/工具协议", ["mcp", "model context protocol"]), ("AI Agent", ["agent", "autonomous", "crew"]), ("RAG/知识库", ["rag", "retrieval", "embedding", "vector"]), ("模型服务/推理", ["inference", "serving", "vllm", "quantization"]), ("多模态/视觉", ["vision", "diffusion", "image generation", "ocr"]), ("数据/评测", ["benchmark", "evaluation", "dataset"]), ("AI应用/产品", ["llm", "llama", "transformer", "generative ai", "chatbot"])]
    for domain, words in rules:
        if any(word in text for word in words):
            return domain
    return "非AI/待复核"


def make_use_case(row: dict[str, Any]) -> str:
    """Create an auditable short explanation without inventing capabilities."""
    domain = row.get("domain") or "项目"
    raw = (row.get("description_raw") or row.get("readme_excerpt") or "").strip()
    if raw:
        return f"主要用于{domain}；仓库简介：{raw}"
    topics = "、".join(row.get("topics") or [])
    if topics:
        return f"主要用于{domain}；主题标签：{topics}"
    return "暂无项目简介，建议打开仓库 README 进一步确认用途。"


def validate(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if payload.get("dataset") != "github_trending_weekly" or not isinstance(rows, list) or not rows:
        raise RuntimeError("GitHub snapshot contract is invalid")
    names = [row.get("full_name") for row in rows]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise RuntimeError("GitHub snapshot contains blank or duplicate repositories")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--date")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--no-readme", action="store_true")
    args = parser.parse_args()
    collect(args.output, date_value=args.date, token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"), limit=args.limit, no_readme=args.no_readme)


if __name__ == "__main__":
    main()

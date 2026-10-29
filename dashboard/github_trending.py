"""Collect the three public GitHub Trending lists without AI filtering."""
from __future__ import annotations

from typing import Any

from github_collector import parse_trending, request_text

from .common import SCHEMA_VERSION, utc_now

PERIODS = ("daily", "weekly", "monthly")
BASE_URL = "https://github.com/trending"


def collect_github_trending(day: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for period in PERIODS:
        url = f"{BASE_URL}?since={period}"
        observed_at = utc_now()
        parsed = parse_trending(request_text(url), url, observed_at)
        if any(row.get("page_stars") is None or row.get("stars_in_period") is None for row in parsed):
            raise ValueError(f"GitHub Trending {period} 缺少 Stars 数据，保留上次完整快照")
        for row in parsed:
            rows.append({
                "period": period,
                "rank": row["rank"],
                "full_name": row["full_name"],
                "url": row["url"],
                "stars": row["page_stars"],
                "new_stars": row["stars_in_period"],
                "description_raw": row["page_description"],
                "source_url": url,
            })
        sources.append({"name": f"GitHub Trending {period}", "url": url, "status": "ok", "tier": 1})
    captured_at = utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": "github_trending_all",
        "snapshot_date": day,
        "as_of": day,
        "generated_at_utc": captured_at,
        "captured_at_utc": captured_at,
        "status": "ok",
        "sources": sources,
        "rows": rows,
        "methodology": "全站 GitHub Trending 原榜单顺序；新增 Stars 直接取对应今日、本周、本月页面显示的期间值。三个榜单每日采集一次；GitHub 未公布固定刷新时间。项目简介保留原文。",
    }

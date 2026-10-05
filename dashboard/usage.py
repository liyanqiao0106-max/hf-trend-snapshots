from __future__ import annotations

import datetime as dt
from typing import Any
from urllib.parse import urlencode

from .common import envelope, request_json

URL = "https://openrouter.ai/api/v1/datasets/rankings-daily"


def monday(value: dt.date) -> dt.date:
    return value - dt.timedelta(days=value.weekday())


def aggregate_weeks(data: list[dict[str, Any]], start: dt.date, today: dt.date, week_count: int = 52) -> list[dict[str, Any]]:
    end_week = monday(today)
    first_week = end_week - dt.timedelta(weeks=week_count - 1)
    daily_models: dict[str, dict[str, int]] = {}
    seen: set[tuple[str, str]] = set()
    for row in data:
        date = str(row.get("date", ""))[:10]
        model = row.get("model_permaslug") or row.get("model") or row.get("id")
        try:
            parsed = dt.date.fromisoformat(date)
            value = int(row["total_tokens"])
        except (ValueError, TypeError, KeyError):
            continue
        if parsed < start or parsed >= today or not model:
            continue
        identity = (date, str(model))
        if identity in seen:
            raise ValueError("Token 数据含重复日期/模型")
        if value < 0:
            raise ValueError("Token 数据含负值")
        seen.add(identity)
        daily_models.setdefault(date, {})[str(model)] = value
    rows: list[dict[str, Any]] = []
    cursor = first_week
    while cursor <= end_week:
        week_end = cursor + dt.timedelta(days=6)
        model_totals: dict[str, int] = {}
        observed_days = 0
        for offset in range(7):
            date = (cursor + dt.timedelta(days=offset)).isoformat()
            if date not in daily_models:
                continue
            observed_days += 1
            for model, value in daily_models[date].items():
                model_totals[model] = model_totals.get(model, 0) + value
        ordered = sorted(model_totals.items(), key=lambda item: item[1], reverse=True)
        total = sum(value for _, value in ordered)
        top20 = [{"id": model, "tokens": str(value), "share": value / total if total else None} for model, value in ordered[:20] if model != "other"]
        top_total = sum(int(item["tokens"]) for item in top20)
        status = "preview" if cursor == end_week else "complete" if observed_days == 7 else "partial"
        rows.append({
            "id": cursor.isoformat(), "week_start": cursor.isoformat(), "week_end": week_end.isoformat(),
            "label": f"{cursor.isoformat()}—{week_end.isoformat()}", "status": status,
            "observed_days": observed_days, "total_tokens": str(total), "top_models": top20,
            "others_tokens": str(max(0, total - top_total)),
        })
        cursor += dt.timedelta(days=7)
    return rows


def collect_usage(day: str, key: str, week_count: int = 52) -> dict[str, Any]:
    today = dt.date.fromisoformat(day)
    first_week = monday(today) - dt.timedelta(weeks=week_count - 1)
    end = today - dt.timedelta(days=1)
    query = urlencode({"start_date": first_week.isoformat(), "end_date": end.isoformat(), "period": "day"})
    payload = request_json(URL + "?" + query, key, cache_key=f"openrouter-rankings-{first_week}-{end}")
    rows = aggregate_weeks(payload.get("data", []), first_week, today, week_count)
    if not rows:
        raise ValueError("OpenRouter 未返回可用的自然周数据")
    completed = [row for row in rows if row["status"] == "complete"]
    latest = completed[-1] if completed else rows[-1]
    result = envelope(
        "token_usage_weekly", "OpenRouter Rankings Daily", "https://openrouter.ai/rankings", rows,
        "按 UTC 周一至周日汇总每日 Rankings 数据。周总量包含每日榜内模型与 other；当前周为 preview，不计算环比。Top 20 之外合并为 Others。",
        snapshot_date=day,
        period={"start": rows[0]["week_start"], "end": rows[-1]["week_end"], "timezone": "UTC"},
        total_tokens=latest["total_tokens"], latest_complete_week=latest["label"],
        source_as_of=(payload.get("meta") or {}).get("as_of"), license="CC BY 4.0",
    )
    if any(row["status"] == "partial" for row in rows[-4:]):
        result["status"] = "partial"
    return result

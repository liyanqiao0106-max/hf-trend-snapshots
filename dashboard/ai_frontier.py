"""Official Hugging Face benchmark scores and Daily Papers, without inferred freshness."""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote, urlparse

from .common import ROOT, envelope, source_record


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else None


def _https_url(value: Any, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    parsed = urlparse(value)
    return value if parsed.scheme == "https" and parsed.netloc else fallback


def collect_ai_frontier(day: str, benchmarks: list[dict[str, str]], paper_limit: int = 20,
                        previous: dict[str, Any] | None = None) -> dict[str, Any]:
    os.environ["HF_HOME"] = str(ROOT / "work/cache/huggingface")
    from huggingface_hub import HfApi

    api = HfApi()
    token: str | bool = os.getenv("HF_TOKEN") or False
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    old_ranks = {(row.get("dataset_id"), row.get("model_id")): row.get("rank")
                 for row in (previous or {}).get("rows", []) if row.get("kind") == "benchmark"}
    for benchmark in benchmarks:
        dataset = benchmark["id"]
        url = f"https://huggingface.co/datasets/{dataset}"
        try:
            entries = api.get_dataset_leaderboard(dataset, token=token, timeout=30)
            count = 0
            for entry in entries[:15]:
                model_id = entry.model_id
                if not model_id or entry.value is None:
                    continue
                model_url = f"https://huggingface.co/{quote(model_id, safe='/')}"
                old_rank = old_ranks.get((dataset, model_id))
                rows.append({"kind": "benchmark", "dimension": benchmark["dimension"], "benchmark": benchmark["label"],
                             "dataset_id": dataset, "rank": entry.rank, "rank_change": old_rank - entry.rank if isinstance(old_rank, int) else None,
                             "model_id": model_id, "score": entry.value,
                             "verified": bool(entry.verified), "source_type": (entry.source or {}).get("name"),
                             "source_url": _https_url((entry.source or {}).get("url"), model_url),
                             "url": model_url, "benchmark_url": url,
                             "result_published_at_utc": None})
                count += 1
            sources.append(source_record(benchmark["label"], url, status="ok" if count else "empty"))
        except Exception as exc:
            sources.append(source_record(benchmark["label"], url, status="error", error=str(exc)[:240]))
    papers_url = "https://huggingface.co/papers"
    try:
        papers = list(api.list_daily_papers(limit=paper_limit, sort="publishedAt", token=token))
        count = 0
        for paper in papers:
            if not paper.id or not paper.title:
                continue
            paper_id = quote(paper.id, safe="")
            rows.append({"kind": "paper", "dimension": "研究论文", "paper_id": paper.id,
                         "title": paper.title, "summary_raw": paper.summary, "published_at_utc": _iso(paper.published_at),
                         "submitted_at_utc": _iso(paper.submitted_at), "upvotes": paper.upvotes,
                         "url": f"https://huggingface.co/papers/{paper_id}", "arxiv_url": f"https://arxiv.org/abs/{paper_id}"})
            count += 1
        sources.append(source_record("Hugging Face Daily Papers", papers_url, status="ok" if count else "empty"))
    except Exception as exc:
        sources.append(source_record("Hugging Face Daily Papers", papers_url, status="error", error=str(exc)[:240]))
    payload = envelope("ai_research_frontier", "Hugging Face official Hub API", "https://huggingface.co/docs/hub/leaderboard-data-guide", rows,
        "榜单分数按原始 benchmark 分别展示，不跨基准聚合；排名变化仅与上次成功快照中同一基准、同一模型比较。保留官方 verified 标记，未验证分数不宣称已复核。榜单接口不提供结果发布日期，故只标采集时间。论文来自 HF Daily Papers，保留原文标题、发布时间和提交时间，不伪造翻译或当日新鲜度。", snapshot_date=day, sources=sources,
        comparison_snapshot_date=(previous or {}).get("snapshot_date"))
    payload["status"] = "partial" if any(source["status"] != "ok" for source in sources) else "ok"
    return payload

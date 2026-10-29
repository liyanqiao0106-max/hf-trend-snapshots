"""Short, source-backed descriptions from public Hugging Face model cards."""

from __future__ import annotations

import concurrent.futures
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any


MISSING = "暂无可核实简介"
USER_AGENT = "hf-trend-snapshots-dashboard/1.0"
CARD_BACKED_SUMMARIES = {
    "BAAI/bge-small-en-v1.5": "BAAI 通用英文文本嵌入模型，用于将查询和文档转成向量并进行语义检索；v1.5 版改善相似度分布。",
    "BAAI/bge-base-en-v1.5": "BAAI 通用英文文本嵌入模型，用于将查询和文档转成向量并进行语义检索；v1.5 版改善相似度分布。",
    "BAAI/bge-large-en-v1.5": "BAAI 通用英文文本嵌入模型，用于将查询和文档转成向量并进行语义检索；v1.5 版改善相似度分布。",
}


def card_excerpt(markdown: str) -> str | None:
    """Keep a short passage that actually describes the model, without inventing a use."""
    body = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", markdown, count=1, flags=re.S)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"!\[[^]]*]\([^)]*\)", "", body)
    body = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", body)
    body = re.sub(r"[*_`]+", "", body)
    candidates = []
    for paragraph in re.split(r"\n\s*\n", body):
        value = " ".join(paragraph.split()).strip(" #>-")
        if len(value) < 25 or len(value) > 2000:
            continue
        if value.startswith(("|", "- ", "<!--", "[!", "http")) or " | " in value[:140] or value[:180].count(" - ") >= 3:
            continue
        if re.match(r"(?i)(?:table of contents|model list|news\b|\d+\.\s+model details)", value):
            continue
        if re.search(r"(?i)\b(model|embedding|encoder|transformer|forecast|generat\w*|recognition|speech|image|ranking|rerank|translation|classification|audio|music|video|dataset|pre-quantized|used for|used to)\b|[\u4e00-\u9fff]{6,}", value) is None:
            continue
        if re.search(r"(?i)\b(update|announcement|check out|click here|test the whole|here's an example|if you are looking)\b", value[:100]):
            continue
        sentences = re.split(r"(?<=[.!?。！？])\s+", value)
        excerpt = " ".join(sentences[:2]).strip()
        candidates.append(excerpt)
        if len(excerpt) >= 120 or len(candidates) >= 2:
            break
    if candidates:
        excerpt = " ".join(candidates)
        return excerpt[:237].rstrip(" ,;:") + ("…" if len(excerpt) > 237 else "")
    return None


def fetch_card(model_id: str) -> tuple[str | None, str]:
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", model_id):
        return None, "invalid_id"
    url = "https://huggingface.co/" + urllib.parse.quote(model_id, safe="/") + "/raw/main/README.md"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read(524_289)
        if len(raw) > 524_288:
            return None, "too_large"
        if model_id in CARD_BACKED_SUMMARIES:
            return CARD_BACKED_SUMMARIES[model_id], "verified"
        excerpt = card_excerpt(raw.decode("utf-8", errors="replace"))
        return (excerpt, "verified") if excerpt else (None, "no_description")
    except urllib.error.HTTPError as exc:
        return None, "missing_card" if exc.code in (404, 410) else "fetch_error"
    except (OSError, ValueError):
        return None, "fetch_error"


def enrich_rows(rows: list[dict[str, Any]], previous: dict[str, Any] | None, day: str, workers: int = 10) -> None:
    old = {row.get("id"): row for row in (previous or {}).get("rows", [])}
    pending = []
    for row in rows:
        row["model_card_url"] = row["model_url"]
        cached = old.get(row["id"], {})
        checked = cached.get("model_card_checked_at")
        try:
            age = (date.fromisoformat(day) - date.fromisoformat(checked)).days if isinstance(checked, str) else 999
        except ValueError:
            age = 999
        if 0 <= age < 28 and cached.get("model_description_status") == "verified":
            row["model_description"] = cached["model_description"]
            row["model_description_status"] = "verified"
            row["model_card_checked_at"] = checked
        else:
            pending.append(row)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda row: fetch_card(row["id"]), pending))
    for row, (excerpt, status) in zip(pending, results):
        row["model_description"] = excerpt or MISSING
        row["model_description_status"] = status
        row["model_card_checked_at"] = day

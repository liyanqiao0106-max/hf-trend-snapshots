from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
UA = "AI-Industry-Research-Dashboard/2.0"
SCHEMA_VERSION = 2


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _cache_paths(cache_key: str) -> tuple[Path, Path]:
    digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    directory = ROOT / "history" / "http-cache"
    return directory / f"{digest}.body", directory / f"{digest}.json"


def request_bytes(
    url: str,
    token: str | None = None,
    accept: str = "application/json",
    retries: int = 3,
    cache_key: str | None = None,
    timeout: int = 60,
) -> bytes:
    """Fetch bytes with bounded retries and an optional conditional-request cache."""
    headers = {"User-Agent": UA, "Accept": accept}
    if token:
        headers["Authorization"] = "Bearer " + token
    body_path = meta_path = None
    if cache_key:
        body_path, meta_path = _cache_paths(cache_key)
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("etag"):
                headers["If-None-Match"] = meta["etag"]
            if meta.get("last_modified"):
                headers["If-Modified-Since"] = meta["last_modified"]
        except (OSError, ValueError):
            pass
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
                raw = response.read()
                if body_path and meta_path:
                    body_path.parent.mkdir(parents=True, exist_ok=True)
                    body_path.write_bytes(raw)
                    write_json(meta_path, {
                        "url": url.split("?")[0],
                        "etag": response.headers.get("ETag"),
                        "last_modified": response.headers.get("Last-Modified"),
                        "stored_at_utc": utc_now(),
                    })
                return raw
        except urllib.error.HTTPError as exc:
            if exc.code == 304 and body_path and body_path.exists():
                return body_path.read_bytes()
            if exc.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise RuntimeError(f"HTTP {exc.code}: {url.split('?')[0]}") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                if body_path and body_path.exists():
                    return body_path.read_bytes()
                raise RuntimeError("无法连接来源: " + url.split("?")[0]) from None
        time.sleep(2**attempt)
    raise RuntimeError("来源请求失败")


def request_json(url: str, token: str | None = None, **kwargs: Any) -> Any:
    return json.loads(request_bytes(url, token, **kwargs))


def write_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(path)


def source_record(name: str, url: str, *, status: str = "ok", tier: int = 1, error: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "url": url, "status": status, "tier": tier}
    if error:
        result["error"] = error
    return result


def envelope(dataset: str, source: str, url: str, rows: list[dict[str, Any]], methodology: str, **extra: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("rows 必须是列表")
    if not rows:
        raise ValueError("来源返回空数据，保留上次成功结果")
    generated = utc_now()
    sources = extra.pop("sources", None) or [source_record(source, url)]
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": dataset,
        "generated_at_utc": generated,
        "collected_at_utc": generated,
        "as_of": extra.get("snapshot_date", generated[:10]),
        "status": "ok",
        "sources": sources,
        "source": source,
        "source_url": url,
        "methodology": methodology,
        "rows": rows,
        **extra,
    }


def archive(directory: str | Path, day: str, dataset: str, payload: dict[str, Any]) -> dict[str, Any]:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    blob = gzip.compress(raw, mtime=0)
    path = Path(directory) / f"{dataset}_{day.replace('-', '')}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    return {"file": path.name, "bytes": len(blob), "raw_bytes": len(raw), "sha256": hashlib.sha256(blob).hexdigest()}


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    low = int(index)
    high = min(low + 1, len(ordered) - 1)
    weight = index - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def compact_price_history(directory: str | Path, current: dict[str, Any], dataset: str, value_key: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for path in sorted(Path(directory).glob(f"{dataset}_*.json.gz"))[-89:]:
        try:
            payload = json.loads(gzip.decompress(path.read_bytes()))
            vals = [float(r[value_key]) for r in payload["rows"] if r.get(value_key) is not None and float(r[value_key]) > 0]
            if vals:
                values.append({"date": payload.get("snapshot_date"), "median": percentile(vals, .5), "sample_count": len(vals)})
        except (ValueError, KeyError, OSError):
            continue
    vals = [float(r[value_key]) for r in current["rows"] if r.get(value_key) is not None and float(r[value_key]) > 0]
    if vals:
        values = [v for v in values if v["date"] != current["snapshot_date"]]
        values.append({"date": current["snapshot_date"], "median": percentile(vals, .5), "sample_count": len(vals)})
    return values

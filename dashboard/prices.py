from __future__ import annotations

import json
import os
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

from .common import UA, envelope, request_json, source_record

MODELS_URL = "https://openrouter.ai/api/v1/models"
AZURE_URL = "https://prices.azure.com/api/retail/prices"
RUNPOD_URL = "https://api.runpod.io/graphql"
VAST_URL = "https://console.vast.ai/api/v0/bundles/"


def _price(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None
    if parsed < 0:
        raise ValueError("dynamic")
    return float(parsed * 1_000_000)


def _optional_price(value: Any) -> float | None:
    try:
        return _price(value)
    except ValueError:
        return None


def parse_models(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("data", []):
        try:
            model_id = item["id"]
            prices = item.get("pricing") or {}
            prompt = _price(prices.get("prompt"))
            output = _price(prices.get("completion"))
        except (KeyError, ValueError):
            continue
        architecture = item.get("architecture") or {}
        top_provider = item.get("top_provider") or {}
        rows.append({
            "id": model_id,
            "name": item.get("name", model_id),
            "vendor": model_id.split("/", 1)[0] if "/" in model_id else "other",
            "url": "https://openrouter.ai/" + model_id,
            "input_usd_per_million": prompt,
            "output_usd_per_million": output,
            "free": prompt == 0 and output == 0,
            "context_length": item.get("context_length"),
            "max_output_tokens": top_provider.get("max_completion_tokens"),
            "input_modalities": architecture.get("input_modalities", []),
            "output_modalities": architecture.get("output_modalities", []),
            "modalities": architecture.get("input_modalities", []),
            "tiered_pricing": bool(prices.get("overrides")),
            "cache_read_usd_per_million": _optional_price(prices.get("input_cache_read")),
            "cache_write_usd_per_million": _optional_price(prices.get("input_cache_write")),
        })
    return sorted(rows, key=lambda row: (
        row["free"],
        row["input_usd_per_million"] if row["input_usd_per_million"] is not None else float("inf"),
        row["id"],
    ))


def collect_models(day: str) -> dict[str, Any]:
    rows = parse_models(request_json(MODELS_URL, cache_key="openrouter-models"))
    result = envelope(
        "token_prices", "OpenRouter model catalog", MODELS_URL, rows,
        "OpenRouter 目录价统一换算为 USD/百万 Token。缺失输入价或输出价保持空值，免费模型单独标记；目录价不是实际成交价。",
        snapshot_date=day, unit="USD / M Tokens",
    )
    vendors: dict[str, list[float]] = {}
    contexts: dict[str, int] = {}
    for row in rows:
        if row["input_usd_per_million"] is not None:
            vendors.setdefault(row["vendor"], []).append(row["input_usd_per_million"])
        length = row.get("context_length")
        bucket = "未知" if not length else "≤32K" if length <= 32768 else "≤128K" if length <= 131072 else ">128K"
        contexts[bucket] = contexts.get(bucket, 0) + 1
    result["vendor_count"] = len({r["vendor"] for r in rows})
    result["context_buckets"] = contexts
    return result


def parse_azure(items: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for item in items:
        product = item.get("productName", "")
        meter = item.get("meterName", "")
        if "Windows" in product or item.get("type") != "Consumption" or item.get("unitOfMeasure") != "1 Hour":
            continue
        if not item.get("isPrimaryMeterRegion", False) or item.get("tierMinimumUnits", 0) != 0:
            continue
        price = float(item.get("retailPrice", 0))
        if price <= 0:
            continue
        kind = "Spot" if "Spot" in meter else "Low Priority" if "Low Priority" in meter else "On-demand"
        row = {
            "id": "azure:" + str(item.get("meterId")), "provider": "Azure", "gpu": config["gpu"],
            "gpu_count": config["gpu_count"], "memory_gb": config.get("memory_gb"),
            "region": item.get("armRegionName", ""), "sku": config["sku"],
            "instance_usd_hour": price, "usd_per_gpu_hour": round(price / config["gpu_count"], 6),
            "billing": kind, "availability": None, "effective_start": item.get("effectiveStartDate"),
            "url": "https://azure.microsoft.com/pricing/details/virtual-machines/linux/",
        }
        rows[(row["region"], kind)] = row
    return list(rows.values())


def _runpod_rows(key: str) -> list[dict[str, Any]]:
    query = "query { gpuTypes { id displayName memoryInGb lowestPrice(input: {gpuCount: 1}) { minimumBidPrice uninterruptablePrice } } }"
    request = urllib.request.Request(RUNPOD_URL, data=json.dumps({"query": query}).encode(), headers={
        "User-Agent": UA, "Content-Type": "application/json", "Authorization": "Bearer " + key,
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    rows = []
    for item in (payload.get("data") or {}).get("gpuTypes", []):
        price = item.get("lowestPrice") or {}
        for billing, value in (("On-demand", price.get("uninterruptablePrice")), ("Spot", price.get("minimumBidPrice"))):
            if value is None or float(value) <= 0:
                continue
            rows.append({"id": f"runpod:{item.get('id')}:{billing}", "provider": "RunPod", "gpu": item.get("displayName") or item.get("id"),
                "gpu_count": 1, "memory_gb": item.get("memoryInGb"), "region": "global", "sku": item.get("id"),
                "instance_usd_hour": float(value), "usd_per_gpu_hour": float(value), "billing": billing,
                "availability": None, "effective_start": None, "url": "https://www.runpod.io/gpu-instance/pricing"})
    return rows


def _vast_rows(key: str) -> list[dict[str, Any]]:
    query = json.dumps({"verified": {"eq": True}, "rentable": {"eq": True}, "type": "on-demand", "order": [["dph_total", "asc"]], "limit": 200})
    url = VAST_URL + "?" + urlencode({"q": query})
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    rows = []
    for item in payload.get("offers", payload.get("results", [])):
        count = int(item.get("num_gpus") or 1)
        total = float(item.get("dph_total") or 0)
        if total <= 0:
            continue
        rows.append({"id": "vast:" + str(item.get("id")), "provider": "Vast.ai", "gpu": item.get("gpu_name") or "GPU",
            "gpu_count": count, "memory_gb": item.get("gpu_ram"), "region": item.get("geolocation") or "unknown",
            "sku": str(item.get("id")), "instance_usd_hour": total, "usd_per_gpu_hour": round(total / count, 6),
            "billing": "On-demand", "availability": item.get("rentable"), "effective_start": None,
            "url": "https://cloud.vast.ai/create/"})
    return rows


def collect_gpu(day: str, configs: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    errors: list[str] = []
    for config in configs:
        query = urlencode({"$filter": f"armSkuName eq '{config['sku']}' and priceType eq 'Consumption'"})
        url = AZURE_URL + "?" + query
        try:
            for page in range(20):
                payload = request_json(url, cache_key=f"azure-{config['sku']}-{page}")
                rows.extend(parse_azure(payload.get("Items", []), config))
                url = payload.get("NextPageLink")
                if not url:
                    break
            else:
                raise RuntimeError("Azure 分页超过上限")
        except Exception as exc:
            errors.append(f"Azure {config['sku']}: {exc}")
    sources.append(source_record("Azure Retail Prices", AZURE_URL, status="ok" if any(r["provider"] == "Azure" for r in rows) else "error"))
    for name, env, url, collector in (
        ("RunPod", "RUNPOD_API_KEY", RUNPOD_URL, _runpod_rows),
        ("Vast.ai", "VAST_API_KEY", VAST_URL, _vast_rows),
    ):
        key = os.environ.get(env)
        if not key:
            sources.append(source_record(name, url, status="not_configured", tier=2))
            continue
        try:
            rows.extend(collector(key))
            sources.append(source_record(name, url))
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            sources.append(source_record(name, url, status="error", error=str(exc)))
    rows.sort(key=lambda row: (row["gpu"], row["provider"], row["billing"], row["usd_per_gpu_hour"]))
    result = envelope(
        "gpu_prices", "Multi-cloud public catalogs", AZURE_URL, rows,
        "实例总价与每 GPU 时价分开保存；多卡实例按 GPU 数折算。On-demand 与 Spot 分开，空缺字段保持空值。",
        snapshot_date=day, unit="USD / GPU·hour", sources=sources, source_errors=errors,
    )
    if errors or any(s["status"] != "ok" for s in sources):
        result["status"] = "partial"
    return result

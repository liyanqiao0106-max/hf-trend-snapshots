from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlencode

from .common import UA, envelope, request_bytes, request_json, source_record, utc_now

MODELS_URL = "https://openrouter.ai/api/v1/models"
AZURE_URL = "https://prices.azure.com/api/retail/prices"
RUNPOD_URL = "https://api.runpod.io/graphql"
VAST_URL = "https://console.vast.ai/api/v0/bundles/"
LAMBDA_URL = "https://lambda.ai/instances"


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
    rows = parse_models(request_json(MODELS_URL, cache_key="openrouter-models", allow_stale_cache=False))
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
        if item.get("currencyCode", "USD") != "USD" or item.get("armSkuName", config["sku"]) != config["sku"]:
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
            "gpu_class": config.get("gpu_class"), "hardware_url": config.get("hardware_url"),
            "region": item.get("armRegionName", ""), "sku": config["sku"],
            "instance_usd_hour": price, "usd_per_gpu_hour": round(price / config["gpu_count"], 6),
            "billing": kind, "availability": None, "effective_start": item.get("effectiveStartDate"),
            "observed_at_utc": utc_now(), "price_basis": "Azure retail USD rate; not a live capacity or executable bid",
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


class _PriceTables(HTMLParser):
    """Extract visible table cells from Lambda's public instance catalog."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[tuple[str | None, list[list[str]]]] = []
        self.tab_labels: dict[str, str] = {}
        self.panel_id: str | None = None
        self.panel_depth = -1
        self.div_depth = 0
        self.table_panel: str | None = None
        self.tab_id: str | None = None
        self.tab_text: list[str] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "div":
            self.div_depth += 1
            if attributes.get("role") == "tabpanel":
                self.panel_id = attributes.get("aria-labelledby")
                self.panel_depth = self.div_depth
        elif tag == "button" and attributes.get("role") == "tab":
            self.tab_id = attributes.get("id")
            self.tab_text = []
        elif tag == "table":
            self.table = []
            self.table_panel = self.panel_id
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
        if self.tab_id is not None:
            self.tab_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self.tab_id is not None:
            self.tab_labels[self.tab_id] = " ".join(" ".join(self.tab_text).split())
            self.tab_id = None
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append((self.table_panel, self.table))
            self.table = None
            self.table_panel = None
        elif tag == "div":
            if self.div_depth == self.panel_depth:
                self.panel_id = None
                self.panel_depth = -1
            self.div_depth -= 1


def parse_lambda_instances(html: str, as_of: str, observed_at_utc: str | None = None) -> list[dict[str, Any]]:
    observed_at_utc = observed_at_utc or utc_now()
    future = re.search(r"These prices take effect ([A-Z][a-z]+ \d{1,2}, \d{4}), at 00:00 UTC", html)
    if future:
        effective = datetime.strptime(future.group(1), "%B %d, %Y").replace(tzinfo=timezone.utc)
        if effective > datetime.fromisoformat(observed_at_utc) or effective.date().isoformat() > as_of:
            raise ValueError("Lambda 公示表仅为未来生效价格，当前价需登录核对")
    parser = _PriceTables()
    parser.feed(html)
    candidates = [table for tab_id, table in parser.tables if parser.tab_labels.get(tab_id) == "1x" and
                  table and len(table[0]) >= 6 and "VRAM/GPU" in table[0][1] and "PRICE/GPU/HR" in table[0][-1]]
    if len(candidates) != 1:
        raise ValueError("Lambda 官方 1x 单卡价格表结构未验证")
    table = candidates[0]
    observed = observed_at_utc
    rows = []
    for cells in table[1:]:
        if len(cells) < 6:
            continue
        match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*GB", cells[1])
        price = re.fullmatch(r"\$(\d+(?:\.\d+)?)", cells[-1])
        if not match or not price:
            continue
        gpu, memory, rate = cells[0], float(match.group(1)), float(price.group(1))
        if rate <= 0:
            continue
        rows.append({"id": "lambda:single:" + re.sub(r"[^a-z0-9]+", "-", gpu.lower()).strip("-"),
            "provider": "Lambda", "gpu": gpu.removeprefix("NVIDIA "), "gpu_count": 1,
            "memory_gb": memory, "region": "unspecified", "sku": gpu,
            "instance_usd_hour": rate, "usd_per_gpu_hour": rate, "billing": "On-demand",
            "availability": None, "effective_start": effective.isoformat() if future else None, "observed_at_utc": observed,
            "url": LAMBDA_URL, "price_basis": "advertised single-GPU instance; CPU/RAM/storage included; tax extra"})
    if not rows:
        raise ValueError("Lambda 官方单卡价格表未解析出报价")
    return rows


def collect_gpu(day: str, configs: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    errors: list[str] = []
    for config in configs:
        query = urlencode({"$filter": f"armSkuName eq '{config['sku']}' and priceType eq 'Consumption'"})
        url = AZURE_URL + "?" + query
        sku_rows: list[dict[str, Any]] = []
        try:
            for page in range(20):
                payload = request_json(url, cache_key=f"azure-{config['sku']}-{page}", allow_stale_cache=False)
                sku_rows.extend(parse_azure(payload.get("Items", []), config))
                url = payload.get("NextPageLink")
                if not url:
                    break
            else:
                raise RuntimeError("Azure 分页超过上限")
            rows.extend(sku_rows)
            status = "ok" if sku_rows else "empty"
            sources.append(source_record("Azure " + config["sku"], AZURE_URL, status=status,
                error="官方零售价格接口未返回符合条件的 USD 小时价" if not sku_rows else None))
        except Exception as exc:
            errors.append(f"Azure {config['sku']}: {exc}")
            sources.append(source_record("Azure " + config["sku"], AZURE_URL, status="error",
                error="官方零售价格接口请求失败"))
    try:
        lambda_rows = parse_lambda_instances(request_bytes(LAMBDA_URL, accept="text/html", allow_stale_cache=False).decode("utf-8"), day)
        rows.extend(lambda_rows)
        sources.append(source_record("Lambda official instances", LAMBDA_URL))
    except Exception as exc:
        errors.append(f"Lambda: {type(exc).__name__}")
        sources.append(source_record("Lambda official instances", LAMBDA_URL, status="error",
            error="官方单卡价格表请求或结构解析失败"))
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
        "Azure 官方零售 USD 小时价及 Lambda 官方单卡实例目录价；GPU 数量和每卡显存来自各自官方规格。Azure Spot 价格可变化，但此零售接口不是实时竞价/成交或可用性证明。effective_start 是价格生效日，不是抓取日；observed_at_utc 才是本次观察时间。Lambda 单卡价格包含该实例 CPU/RAM/存储，税费可能另计。多卡实例按 GPU 数折算，On-demand/Spot/Low Priority 分开；缺失型号逐 SKU 标记。",
        snapshot_date=day, unit="USD / GPU·hour", sources=sources, source_errors=errors,
    )
    if errors or any(s["status"] != "ok" for s in sources):
        result["status"] = "partial"
    return result

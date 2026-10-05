from __future__ import annotations

import datetime as dt
import re
from typing import Any
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .common import envelope, request_bytes, request_json, source_record

BLS_SERIES = "PCU3341123341121"
BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/" + BLS_SERIES
DRAMEXCHANGE_URL = "https://www.dramexchange.com/"

MEMORY_MATCHES = [
    ("DRAM", "DDR5 16Gb (2Gx8) 4800", "DDR5 16Gb chip"),
    ("DRAM", "DDR4 16Gb (2Gx8) 3200", "DDR4 16Gb chip"),
    ("DRAM", "DDR4 8Gb (1Gx8) 3200", "DDR4 8Gb chip"),
    ("DRAM module", "DDR5 UDIMM 16GB", "DDR5 UDIMM 16GB"),
    ("DRAM module", "DDR5 RDIMM 32GB", "DDR5 RDIMM 32GB"),
    ("DRAM module", "DDR4 UDIMM 16GB", "DDR4 UDIMM 16GB"),
    ("NAND", "SLC 2Gb", "SLC NAND 2Gb"),
    ("NAND", "MLC 64Gb", "MLC NAND 64Gb"),
    ("NAND wafer", "512Gb TLC", "TLC NAND wafer 512Gb"),
    ("NAND wafer", "256Gb TLC", "TLC NAND wafer 256Gb"),
    ("NAND wafer", "128Gb TLC", "TLC NAND wafer 128Gb"),
    ("GDDR", "GDDR5 8Gb", "GDDR5 8Gb"),
    ("GDDR", "GDDR6 8Gb", "GDDR6 8Gb"),
]


def _number(value: str) -> float | None:
    cleaned = value.replace(",", "").replace("$", "").strip()
    found = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    try:
        return float(found.group()) if found else None
    except ValueError:
        return None


def parse_dramexchange(raw: bytes, day: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(raw, "html.parser")
    tables: list[tuple[list[str], str]] = []
    for tr in soup.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["td", "th"])]
        if len(cells) >= 6:
            tables.append((cells, " ".join(cells).lower().replace(" ", "")))
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for category, match, label in MEMORY_MATCHES:
        needle = match.lower().replace(" ", "")
        for cells, compact in tables:
            if needle not in compact:
                continue
            price = _number(cells[5]) if len(cells) > 5 else None
            if price is None or price <= 0:
                continue
            row_id = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
            rows.append({"id": "trendforce:" + row_id, "category": category, "item": label,
                "price": price, "currency": "USD", "unit": "per chip/module/wafer",
                "quote_type": "spot_session_average", "market": "industry spot",
                "as_of": day, "url": DRAMEXCHANGE_URL, "source": "DRAMeXchange/TrendForce public table"})
            seen.add(row_id)
            break
    # SSD street-price rows use Brand / Interface / Series / Capacity / High / Low / Avg.
    for cells, compact in tables:
        if len(cells) < 7 or len(cells) > 10 or not re.search(r"\b(?:SATA|PCIe)\b", " ".join(cells), re.I):
            continue
        capacity = next((cell for cell in cells[:5] if re.fullmatch(r"\s*[\d.]+\s*(?:GB|TB)\s*", cell, re.I)), "")
        if not capacity:
            continue
        price = _number(cells[6])
        if price is None or price <= 0:
            continue
        item = " ".join(cells[:4])
        capacity_tb = None
        matched = re.search(r"([\d.]+)\s*(TB|GB)", capacity, re.I)
        if matched:
            capacity_tb = float(matched.group(1)) * (1 if matched.group(2).upper() == "TB" else 1 / 1000)
        row_id = "ssd-" + re.sub(r"[^a-z0-9]+", "-", item.lower()).strip("-")
        if row_id in seen:
            continue
        seen.add(row_id)
        rows.append({"id": "trendforce:" + row_id, "category": "SSD", "item": item,
            "price": price, "currency": "USD", "unit": "per drive", "usd_per_tb": round(price / capacity_tb, 4) if capacity_tb else None,
            "quote_type": "street_average", "market": "retail street", "as_of": day,
            "url": DRAMEXCHANGE_URL, "source": "DRAMeXchange/TrendForce public table"})
    return rows


def parse_bls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    series = ((payload.get("Results") or {}).get("series") or [])
    if not series:
        raise ValueError("BLS 未返回存储设备 PPI 序列")
    points: list[dict[str, Any]] = []
    for item in series[0].get("data", []):
        period = item.get("period", "")
        if not period.startswith("M") or period == "M13":
            continue
        try:
            date = f"{int(item['year']):04d}-{int(period[1:]):02d}-01"
            points.append({"date": date, "value": float(item["value"])})
        except (ValueError, KeyError, TypeError):
            continue
    points.sort(key=lambda row: row["date"])
    by_date = {row["date"]: row["value"] for row in points}
    for row in points:
        date = dt.date.fromisoformat(row["date"])
        previous_month = (date - dt.timedelta(days=1)).replace(day=1).isoformat()
        previous_year = date.replace(year=date.year - 1).isoformat()
        before, year_before = by_date.get(previous_month), by_date.get(previous_year)
        row["mom_percent"] = None if before in (None, 0) else round((row["value"] / before - 1) * 100, 3)
        row["yoy_percent"] = None if year_before in (None, 0) else round((row["value"] / year_before - 1) * 100, 3)
    return points


def hbm_rental_rows(gpu_payload: dict[str, Any] | None, day: str) -> list[dict[str, Any]]:
    rows = []
    for quote in (gpu_payload or {}).get("rows", []):
        memory = quote.get("memory_gb")
        price = quote.get("usd_per_gpu_hour")
        if not memory or price is None or not re.search(r"\b(?:H100|H200|A100|B200|MI300)\b", quote.get("gpu", ""), re.I):
            continue
        rows.append({"id": "hbm:" + quote["id"], "category": "HBM rental proxy",
            "item": f"{quote['gpu']} · {quote['provider']} · {quote['region']} · {quote['billing']}",
            "price": round(float(price) / float(memory), 8), "currency": "USD", "unit": "per HBM-GB·hour",
            "quote_type": "compute_inclusive_rental_proxy", "market": "cloud rental",
            "as_of": day, "url": quote.get("url"), "source": quote.get("provider"),
            "note": "由云 GPU 每小时价格除以显存容量得到，包含 GPU 计算、CPU、RAM 与平台成本，不是纯 HBM 租价。"})
    return rows


def attach_history(rows: list[dict[str, Any]], previous: dict[str, Any] | None, day: str) -> None:
    old = {row.get("id"): row for row in (previous or {}).get("rows", [])}
    for row in rows:
        points = list((old.get(row["id"]) or {}).get("history", []))[-179:]
        points = [point for point in points if point.get("date") != day]
        points.append({"date": day, "price": row.get("price")})
        row["history"] = points
        if len(points) >= 2 and points[-2].get("price") not in (None, 0):
            row["change_percent"] = round((row["price"] / points[-2]["price"] - 1) * 100, 3)
        else:
            row["change_percent"] = None


def collect_storage(day: str, gpu_payload: dict[str, Any] | None = None, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    try:
        rows.extend(parse_dramexchange(request_bytes(DRAMEXCHANGE_URL, accept="text/html,*/*", cache_key="dramexchange-home"), day))
        sources.append(source_record("DRAMeXchange/TrendForce public tables", DRAMEXCHANGE_URL))
    except Exception as exc:
        errors.append("DRAMeXchange: " + str(exc))
        sources.append(source_record("DRAMeXchange/TrendForce public tables", DRAMEXCHANGE_URL, status="error", error=str(exc)))
    rows.extend(hbm_rental_rows(gpu_payload, day))
    if gpu_payload:
        sources.append(source_record("Cloud GPU catalogs (HBM rental proxy)", gpu_payload.get("source_url", ""), status=gpu_payload.get("status", "ok")))
    current_year = dt.date.fromisoformat(day).year
    bls_points: list[dict[str, Any]] = []
    try:
        url = BLS_URL + "?" + urlencode({"startyear": max(2016, current_year - 10), "endyear": current_year})
        bls_points = parse_bls(request_json(url, cache_key=f"bls-{BLS_SERIES}"))
        sources.append(source_record("U.S. BLS Storage Device PPI", BLS_URL))
    except Exception as exc:
        errors.append("BLS: " + str(exc))
        sources.append(source_record("U.S. BLS Storage Device PPI", BLS_URL, status="error", error=str(exc)))
    if not rows and bls_points:
        latest = bls_points[-1]
        rows.append({"id": "bls:" + BLS_SERIES, "category": "Storage PPI", "item": "Computer storage devices PPI",
            "price": latest["value"], "currency": "index", "unit": "Dec 2004=100", "quote_type": "monthly_price_index",
            "market": "US producer prices", "as_of": latest["date"], "url": BLS_URL, "source": "U.S. BLS"})
    attach_history(rows, previous, day)
    result = envelope("storage_hardware_prices", "DRAMeXchange + cloud catalogs + BLS", DRAMEXCHANGE_URL, rows,
        "公开表的 Session Average/Street Average 每日保存为自建历史；HBM 项为含计算成本的租赁代理；BLS 仅作月度行业指数。板块不收录新闻。",
        snapshot_date=day, sources=sources, source_errors=errors, ppi_series=bls_points)
    if errors or any(source["status"] != "ok" for source in sources):
        result["status"] = "partial"
    return result

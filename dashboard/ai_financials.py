"""Auditable SEC whole-company financial facts and period-matched calculations.

SEC Company Facts omits company-specific tags. A missing standard fact does not
prove that the company did not disclose the value in its original filing.
"""
from __future__ import annotations

import os
import re
from datetime import date
from typing import Any

from .common import ROOT, envelope, source_record


CONCEPTS = {
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",),
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "Revenue"),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities", "CashFlowsFromUsedInOperatingActivities"),
    "operating_income": ("OperatingIncomeLoss", "ProfitLossFromOperatingActivities"),
}
FORMULAS = {
    "revenue_yoy": "(revenue / prior_revenue - 1) * 100",
    "capex_yoy": "(capex / prior_capex - 1) * 100",
    "capex_to_revenue": "capex / revenue * 100",
    "capex_to_ocf": "capex / operating_cash_flow * 100",
    "free_cash_flow": "operating_cash_flow - capex",
    "free_cash_flow_margin": "(operating_cash_flow - capex) / revenue * 100",
    "operating_margin": "operating_income / revenue * 100",
}
METRIC_KEYS = tuple(CONCEPTS) + tuple(FORMULAS)
PERIOD_TYPES = ("FY", "TTM", "Quarter", "YTD")
FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "20-F/A", "40-F", "40-F/A"}
TAXONOMIES = {"us-gaap", "ifrs-full"}


def _date(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, date) else (str(value) if value else None)


def _days(start: str, end: str) -> int:
    return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1


def _period_type(start: str, end: str, form: str) -> str | None:
    days = _days(start, end)
    if 330 <= days <= 385 and form.startswith(("10-K", "20-F", "40-F")):
        return "FY"
    if 75 <= days <= 105:
        return "Quarter"
    if 106 <= days <= 329 and form.startswith("10-Q"):
        return "YTD"
    return None


def _fact(fact: Any, names: tuple[str, ...], cik: int, as_of: str | None = None) -> dict[str, Any] | None:
    concept = str(getattr(fact, "concept", ""))
    prefix, separator, tag = concept.partition(":")
    taxonomy = prefix if separator else str(getattr(fact, "taxonomy", ""))
    tag = tag if separator else concept
    if taxonomy not in TAXONOMIES or tag not in names:
        return None
    form = str(getattr(fact, "form_type", ""))
    if form not in FORMS or getattr(fact, "dimensions", None):
        return None
    start, end = _date(getattr(fact, "period_start", None)), _date(getattr(fact, "period_end", None))
    filed = _date(getattr(fact, "filing_date", None))
    value, currency = getattr(fact, "numeric_value", None), str(getattr(fact, "unit", ""))
    if value is None or currency != "USD" or not start or not end or (as_of and filed and filed > as_of):
        return None
    try:
        ptype = _period_type(start, end, form)
    except ValueError:
        return None
    if ptype is None:
        return None
    accession = str(getattr(fact, "accession", "") or "")
    url = (f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession}-index.html"
           if re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession) else None)
    return {
        "value_usd": float(value), "value_pct": None, "status": "ok", "missing_reason": None,
        "concept": f"{taxonomy}:{tag}", "taxonomy_tag": f"{taxonomy}:{tag}", "period_start": start, "period_end": end,
        "period_type": ptype, "fiscal_year": getattr(fact, "fiscal_year", None),
        "fiscal_quarter": getattr(fact, "fiscal_period", None), "filing_date": filed,
        "form": form, "accession": accession, "accession_number": accession,
        "filing_url": url, "source_url": url, "source_type": "Reported",
        "currency": currency, "unit": currency, "formula": None, "inputs": None,
    }


def _facts(facts: list[Any], names: tuple[str, ...], cik: int, as_of: str | None = None) -> list[dict[str, Any]]:
    result = [record for raw in facts if (record := _fact(raw, names, cik, as_of))]
    result.sort(key=lambda x: (x["period_end"], x["filing_date"] or "", -names.index(x["concept"].split(":", 1)[1])), reverse=True)
    return result


def _metric(facts: list[Any], names: tuple[str, ...], cik: int) -> dict[str, Any] | None:
    """Retain the old helper interface for latest individual reported fact."""
    result = _facts(facts, names, cik)
    return result[0] if result else None


def _drop_stale_capex(metrics: dict[str, dict[str, Any] | None]) -> tuple[dict[str, dict[str, Any] | None], list[dict[str, Any]]]:
    capex = metrics.get("capex")
    ends = [m["period_end"] for m in metrics.values() if m and m.get("period_end")]
    if not capex or not ends:
        return metrics, []
    try:
        stale = (date.fromisoformat(max(ends)) - date.fromisoformat(capex["period_end"])).days > 370
    except (TypeError, ValueError):
        stale = False
    if not stale:
        return metrics, []
    omitted = {"metric": "capex", "reason": "标准化资本开支标签过期；Company Facts 可能遗漏公司自定义标签。", **capex}
    metrics["capex"] = None
    return metrics, [omitted]


def _missing(reason: str, *, key: str = "", status: str = "missing") -> dict[str, Any]:
    return {
        "value_usd": None, "value_pct": None, "status": status, "missing_reason": reason,
        "concept": None, "taxonomy_tag": None, "period_start": None, "period_end": None,
        "period_type": None, "fiscal_year": None, "fiscal_quarter": None,
        "filing_date": None, "form": None, "accession": None, "accession_number": None,
        "filing_url": None, "source_url": None, "source_type": "Derived" if key in FORMULAS else "Reported",
        "currency": "USD", "unit": "USD", "formula": FORMULAS.get(key), "inputs": None,
    }


def _audit(metric: dict[str, Any]) -> dict[str, Any]:
    return {key: metric.get(key) for key in ("value_usd", "value_pct", "period_start", "period_end",
            "filing_date", "form", "accession", "filing_url", "concept", "source_type")}


def _prior(items: list[dict[str, Any]], current: dict[str, Any], key: str) -> dict[str, Any]:
    for item in items:
        start_gap = (date.fromisoformat(current["period_start"]) - date.fromisoformat(item["period_start"])).days
        end_gap = (date.fromisoformat(current["period_end"]) - date.fromisoformat(item["period_end"])).days
        if item["period_type"] == current["period_type"] and 357 <= start_gap <= 373 and 357 <= end_gap <= 373 and abs(_days(current["period_start"], current["period_end"]) - _days(item["period_start"], item["period_end"])) <= 8:
            return item
    return _missing("无可比的上年同期标准事实", key=key)


def _derive(key: str, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing = [name for name, item in inputs.items() if item["status"] != "ok"]
    if missing:
        return _missing("基础指标缺失：" + "、".join(missing), key=key)
    current = [item for name, item in inputs.items() if not name.startswith("prior_")]
    if len({(item["period_start"], item["period_end"], item["currency"]) for item in current}) != 1:
        return _missing("基础指标期间或币种不一致", key=key)
    values = {name: item["value_usd"] for name, item in inputs.items()}
    denominator = {
        "revenue_yoy": values.get("prior_revenue"), "capex_yoy": values.get("prior_capex"),
        "capex_to_revenue": values.get("revenue"), "capex_to_ocf": values.get("operating_cash_flow"),
        "free_cash_flow_margin": values.get("revenue"), "operating_margin": values.get("revenue"),
    }.get(key)
    if denominator is not None and denominator <= 0:
        reason = "经营现金流为负，覆盖率无通常解释意义（N/M）" if key == "capex_to_ocf" and denominator < 0 else "分母为零或负值，比例不具可比意义"
        return _missing(reason, key=key)
    if key == "free_cash_flow":
        result = values["operating_cash_flow"] - values["capex"]
    elif key.endswith("_yoy"):
        base = "revenue" if key == "revenue_yoy" else "capex"
        result = (values[base] / values["prior_" + base] - 1) * 100
    elif key == "free_cash_flow_margin":
        result = (values["operating_cash_flow"] - values["capex"]) / values["revenue"] * 100
    else:
        numerator = {"capex_to_revenue": "capex", "capex_to_ocf": "capex", "operating_margin": "operating_income"}[key]
        result = values[numerator] / denominator * 100
    representative = current[0]
    return {
        **_missing("", key=key), "value_usd": result if key == "free_cash_flow" else None,
        "value_pct": None if key == "free_cash_flow" else result, "status": "ok", "missing_reason": None,
        "period_start": representative["period_start"], "period_end": representative["period_end"],
        "period_type": representative["period_type"], "fiscal_year": representative["fiscal_year"],
        "fiscal_quarter": representative["fiscal_quarter"],
        "inputs": {name: _audit(item) for name, item in inputs.items()},
    }


def _period(facts_by_key: dict[str, list[dict[str, Any]]], ptype: str) -> dict[str, Any]:
    if ptype == "TTM":
        reason = "无法从 Company Facts 安全核验滚动十二个月；暂不推算"
        return {"label": ptype, "period_start": None, "period_end": None, "status": "missing", "missing_reason": reason,
                "metrics": {key: _missing(reason, key=key) for key in METRIC_KEYS}}
    anchors = [m for m in facts_by_key["revenue"] if m["period_type"] == ptype]
    if not anchors:
        anchors = sorted((m for items in facts_by_key.values() for m in items if m["period_type"] == ptype),
                         key=lambda m: (m["period_end"], m["filing_date"] or ""), reverse=True)
    if not anchors:
        reason = "SEC 标准化公司事实中没有该期间的可用 USD 全实体数据"
        return {"label": ptype, "period_start": None, "period_end": None, "status": "missing", "missing_reason": reason,
                "metrics": {key: _missing(reason, key=key) for key in METRIC_KEYS}}
    anchor = anchors[0]
    start, end = anchor["period_start"], anchor["period_end"]
    metrics = {}
    for key, items in facts_by_key.items():
        match = next((m for m in items if (m["period_start"], m["period_end"]) == (start, end)), None)
        reason = ("仅有其他期间标准标签，不能代替本期；可能存在公司自定义标签" if items else
                  "Company Facts 未匹配全实体 USD 标准标签；可能存在自定义标签或不同币种")
        metrics[key] = match or _missing(reason, key=key)
    for key, base in (("revenue_yoy", "revenue"), ("capex_yoy", "capex")):
        prior = _prior(facts_by_key[base], metrics[base], key) if metrics[base]["status"] == "ok" else _missing("本期基础值缺失", key=key)
        metrics[key] = _derive(key, {base: metrics[base], "prior_" + base: prior})
    for key, bases in {
        "capex_to_revenue": ("capex", "revenue"), "capex_to_ocf": ("capex", "operating_cash_flow"),
        "free_cash_flow": ("operating_cash_flow", "capex"),
        "free_cash_flow_margin": ("operating_cash_flow", "capex", "revenue"),
        "operating_margin": ("operating_income", "revenue"),
    }.items():
        metrics[key] = _derive(key, {base: metrics[base] for base in bases})
    return {"label": ptype, "period_start": start, "period_end": end,
            "status": "ok" if all(m["status"] == "ok" for m in metrics.values()) else "partial",
            "missing_reason": None, "metrics": metrics}


def _empty_row(item: dict[str, str], reason: str, *, cik: int | None = None) -> dict[str, Any]:
    periods = {ptype: _period({key: [] for key in CONCEPTS}, ptype) for ptype in PERIOD_TYPES}
    for period in periods.values():
        period["status"], period["missing_reason"] = "unavailable", reason
        for metric in period["metrics"].values():
            metric["status"], metric["missing_reason"] = "unavailable", reason
    return {"ticker": item["ticker"], "company": item["name"], "sector_group": item.get("sector_group"),
            "reporting_standard": item.get("reporting_standard"), "cik": cik,
            "company_url": f"https://www.sec.gov/edgar/browse/?CIK={cik or item['ticker']}",
            "status": "unavailable", "missing_reason": reason, "periods": periods,
            "metrics": periods["FY"]["metrics"], "omitted_metrics": []}


def collect_ai_financials(day: str, companies: list[dict[str, str]]) -> dict[str, Any]:
    # edgartools initializes paths at import time; keep all caches in work/.
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(ROOT / "work/cache/edgar-data")
    os.environ["EDGAR_CACHE_DIR"] = str(ROOT / "work/cache/edgar")
    identity = os.getenv("SEC_USER_AGENT")
    if not identity:
        raise ValueError("SEC_USER_AGENT 未配置；需设置可联系的 SEC 抓取身份")
    from edgar import Company, set_identity

    set_identity(identity)
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for item in companies:
        ticker = item["ticker"]
        cik: int | None = None
        try:
            company = Company(ticker)
            cik = int(company.cik)
            entity_facts = company.get_facts()
            if entity_facts is None:
                raise ValueError("SEC 未返回 Company Facts")
            facts = entity_facts.get_all_facts()
            by_key = {key: _facts(facts, names, cik, day) for key, names in CONCEPTS.items()}
            periods = {ptype: _period(by_key, ptype) for ptype in PERIOD_TYPES}
            # Derive the displayed reporting standard from the FY facts actually
            # selected; do not assume a foreign issuer's taxonomy from ticker.
            fy_taxonomies = {m["concept"].split(":", 1)[0] for m in periods["FY"]["metrics"].values()
                             if m["status"] == "ok" and m["source_type"] == "Reported"}
            reporting_standard = ({"us-gaap": "US GAAP", "ifrs-full": "IFRS"}.get(next(iter(fy_taxonomies)))
                                  if len(fy_taxonomies) == 1 else "unknown")
            latest_capex = by_key["capex"][0] if by_key["capex"] else None
            latest_other = max((m["period_end"] for key, items in by_key.items() if key != "capex" for m in items), default=None)
            omitted = []
            if latest_capex and latest_other and (date.fromisoformat(latest_other) - date.fromisoformat(latest_capex["period_end"])).days > 370:
                omitted = [{"metric": "capex", "reason": "标准标签过期；Company Facts 不收录自定义标签", **latest_capex}]
            status = "ok" if periods["FY"]["status"] == "ok" else "partial"
            rows.append({"ticker": ticker, "company": item["name"], "sector_group": item.get("sector_group"),
                "reporting_standard": reporting_standard, "cik": cik, "status": status,
                "missing_reason": None, "company_url": f"https://www.sec.gov/edgar/browse/?CIK={cik}",
                "periods": periods, "metrics": periods["FY"]["metrics"], "omitted_metrics": omitted})
            sources.append(source_record(ticker, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
                status=status, error="部分标准标签或同期事实不可用；请见每项缺失原因" if status != "ok" else None))
        except Exception as exc:
            # Do not serialize exception messages: an HTTP client could include
            # request headers, including the configured SEC contact identity.
            reason = "SEC 公司事实请求失败或解析异常（" + type(exc).__name__ + "）"
            rows.append(_empty_row(item, reason, cik=cik))
            source_url = (f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json" if cik else
                          f"https://www.sec.gov/edgar/browse/?CIK={ticker}")
            sources.append(source_record(ticker, source_url, status="error", error=reason))
    payload = envelope("ai_company_financials", "SEC EDGAR XBRL via edgartools",
        "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", rows,
        "SEC 全公司非自定义 US-GAAP/IFRS XBRL 事实；每项独立保存期间与原件。CapEx 是现金购建物业、厂房及设备支出，不等于 AI 专项资本开支。FY 默认；YTD 为累计期；仅同期可靠 USD 基础值计算 Derived。TTM 暂不推算。Company Facts 缺失不等于未披露。",
        snapshot_date=day, default_period="FY", available_periods=list(PERIOD_TYPES),
        metric_keys=list(METRIC_KEYS), sources=sources)
    payload["status"] = "partial" if any(s["status"] != "ok" for s in sources) else "ok"
    return payload

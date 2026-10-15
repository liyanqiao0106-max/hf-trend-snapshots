"""Daily SEC company-wide financial facts via edgartools, not AI-only estimates."""
from __future__ import annotations

import os
import re
from datetime import date
from typing import Any

from .common import ROOT, envelope, source_record


CONCEPTS = {
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",),
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
}


def _date(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, date) else (str(value) if value else None)


def _metric(facts: list[Any], names: tuple[str, ...], cik: int) -> dict[str, Any] | None:
    matches = []
    for fact in facts:
        concept = str(getattr(fact, "concept", ""))
        if concept.split(":")[-1] not in names:
            continue
        if getattr(fact, "form_type", "") not in ("10-K", "10-Q"):
            continue
        value = getattr(fact, "numeric_value", None)
        if value is None or getattr(fact, "unit", "") != "USD":
            continue
        if not getattr(fact, "period_start", None) or not getattr(fact, "period_end", None):
            continue
        if getattr(fact, "dimensions", None):
            continue
        matches.append(fact)
    if not matches:
        return None
    matches.sort(key=lambda item: (_date(item.period_end) or "", _date(item.filing_date) or "", -names.index(str(item.concept).split(":")[-1])), reverse=True)
    fact = matches[0]
    accession = str(fact.accession or "")
    filing_url = (f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{accession}-index.html"
                  if re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession) else None)
    return {
        "value_usd": float(fact.numeric_value), "concept": str(fact.concept),
        "period_start": _date(fact.period_start), "period_end": _date(fact.period_end),
        "filing_date": _date(fact.filing_date), "form": str(fact.form_type),
        "accession": accession, "filing_url": filing_url,
    }


def collect_ai_financials(day: str, companies: list[dict[str, str]]) -> dict[str, Any]:
    # edgartools otherwise creates ~/.edgar; constrain its data and HTTP cache to this project.
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
        try:
            company = Company(ticker)
            cik = int(company.cik)
            entity_facts = company.get_facts()
            if entity_facts is None:
                raise ValueError("SEC 未返回 company facts")
            facts = entity_facts.get_all_facts()
            metrics = {key: _metric(facts, concepts, cik) for key, concepts in CONCEPTS.items()}
            if not any(metrics.values()):
                raise ValueError("未找到可用的 USD 标准化财务事实")
            rows.append({"ticker": ticker, "company": item["name"], "cik": cik, "metrics": metrics,
                         "company_url": f"https://www.sec.gov/edgar/browse/?CIK={cik}"})
            sources.append(source_record(ticker, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"))
        except Exception as exc:
            sources.append(source_record(ticker, f"https://www.sec.gov/edgar/browse/?CIK={ticker}", status="error", error=str(exc)[:240]))
    payload = envelope("ai_company_financials", "SEC EDGAR XBRL via edgartools", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", rows,
        "仅展示 SEC 全公司标准化 USD XBRL 事实。资本开支是现金流量表购建物业、厂房与设备支出，不等于 AI 专项资本开支；10-Q 通常为财年累计，10-K 为全年。各指标保留独立报告区间和申报日期，不跨期相加或混算同比。", snapshot_date=day, sources=sources)
    payload["status"] = "partial" if any(source["status"] != "ok" for source in sources) else "ok"
    return payload

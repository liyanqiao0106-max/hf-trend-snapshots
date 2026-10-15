import datetime as dt
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from dashboard.ai_financials import _drop_stale_capex, _metric, collect_ai_financials
from dashboard.ai_frontier import collect_ai_frontier


def fact(concept, value, end, filed="2026-09-01", start="2026-01-01", form="10-Q"):
    return SimpleNamespace(concept="us-gaap:" + concept, numeric_value=value, unit="USD",
        period_start=dt.date.fromisoformat(start), period_end=dt.date.fromisoformat(end),
        filing_date=dt.date.fromisoformat(filed), form_type=form, dimensions=None,
        accession="0000123456-26-000001")


class AiObservatoryTests(unittest.TestCase):
    def test_sec_requires_explicit_contact_identity_before_network(self):
        with patch.dict(os.environ, {"SEC_USER_AGENT": ""}):
            with self.assertRaisesRegex(ValueError, "SEC_USER_AGENT"):
                collect_ai_financials("2026-10-14", [{"ticker": "NVDA", "name": "NVIDIA"}])

    def test_sec_metric_uses_latest_period_not_latest_restatement(self):
        facts = [fact("PaymentsToAcquirePropertyPlantAndEquipment", 10, "2025-12-31", "2026-10-01"),
                 fact("PaymentsToAcquirePropertyPlantAndEquipment", 20, "2026-06-30", "2026-08-01")]
        metric = _metric(facts, ("PaymentsToAcquirePropertyPlantAndEquipment",), 123456)
        self.assertEqual(metric["value_usd"], 20)
        self.assertEqual(metric["period_start"], "2026-01-01")
        self.assertIn("000012345626000001", metric["filing_url"])

    def test_stale_capex_tag_is_retained_for_audit_but_not_presented_as_current(self):
        metrics = {"capex": _metric([fact("PaymentsToAcquirePropertyPlantAndEquipment", 10, "2020-06-30")], ("PaymentsToAcquirePropertyPlantAndEquipment",), 123456),
                   "revenue": _metric([fact("Revenues", 20, "2026-06-30")], ("Revenues",), 123456), "operating_cash_flow": None}
        sanitized, omitted = _drop_stale_capex(metrics)
        self.assertIsNone(sanitized["capex"])
        self.assertEqual(omitted[0]["metric"], "capex")
        self.assertEqual(omitted[0]["period_end"], "2020-06-30")

    def test_sec_collector_keeps_partial_and_does_not_infer_ai_capex(self):
        company = SimpleNamespace(cik=123456, get_facts=lambda: SimpleNamespace(get_all_facts=lambda: [
            fact("PaymentsToAcquirePropertyPlantAndEquipment", 2e9, "2026-06-30")]))
        def lookup(ticker):
            if ticker == "BAD":
                raise RuntimeError("SEC unavailable")
            return company
        with patch.dict(os.environ, {"SEC_USER_AGENT": "Test User test@example.com", "EDGAR_LOCAL_DATA_DIR": str(Path(__file__).resolve().parents[1] / "work/cache/edgar-data"), "EDGAR_CACHE_DIR": str(Path(__file__).resolve().parents[1] / "work/cache/edgar")}), patch("edgar.Company", side_effect=lookup), patch("edgar.set_identity"):
            payload = collect_ai_financials("2026-10-14", [{"ticker": "GOOD", "name": "Good"}, {"ticker": "BAD", "name": "Bad"}])
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["rows"][0]["metrics"]["capex"]["value_usd"], 2e9)
        self.assertIsNone(payload["rows"][0]["metrics"]["revenue"])
        self.assertEqual(payload["sources"][1]["status"], "error")
        self.assertIn("不等于 AI 专项", payload["methodology"])

    def test_frontier_keeps_verification_and_real_paper_dates(self):
        entry = SimpleNamespace(rank=1, model_id="org/model", value=83.2, verified=False,
            source={"name": "Model card", "url": "https://huggingface.co/org/model"})
        paper = SimpleNamespace(id="2601.12345", title="An AI Paper", summary="English summary",
            published_at=dt.datetime(2026, 10, 10, tzinfo=dt.timezone.utc),
            submitted_at=dt.datetime(2026, 10, 11, tzinfo=dt.timezone.utc), upvotes=5)
        with patch("huggingface_hub.HfApi") as api_class:
            api_class.return_value.get_dataset_leaderboard.return_value = [entry]
            api_class.return_value.list_daily_papers.return_value = [paper]
            payload = collect_ai_frontier("2026-10-14", [{"id": "SWE-bench/SWE-bench_Verified", "label": "SWE", "dimension": "代码智能体"}], 20,
                {"snapshot_date": "2026-10-13", "rows": [{"kind": "benchmark", "dataset_id": "SWE-bench/SWE-bench_Verified", "model_id": "org/model", "rank": 3}]})
        score, publication = payload["rows"]
        self.assertFalse(score["verified"])
        self.assertEqual(score["rank_change"], 2)
        self.assertEqual(payload["comparison_snapshot_date"], "2026-10-13")
        self.assertIsNone(score["result_published_at_utc"])
        self.assertEqual(publication["summary_raw"], "English summary")
        self.assertEqual(publication["published_at_utc"], "2026-10-10T00:00:00+00:00")
        self.assertEqual(payload["status"], "ok")

    def test_frontier_marks_empty_source_partial(self):
        with patch("huggingface_hub.HfApi") as api_class:
            api_class.return_value.get_dataset_leaderboard.return_value = []
            api_class.return_value.list_daily_papers.return_value = [SimpleNamespace(id="2601.12345", title="Paper", summary=None, published_at=None, submitted_at=None, upvotes=None)]
            payload = collect_ai_frontier("2026-10-14", [{"id": "x/y", "label": "X", "dimension": "代码智能体"}], 20)
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["sources"][0]["status"], "empty")


if __name__ == "__main__":
    unittest.main()

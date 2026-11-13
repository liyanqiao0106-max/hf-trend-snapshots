import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from dashboard.common import request_bytes
from dashboard.storage_market import attach_history, collect_storage, parse_dramexchange, parse_samsung_ssd
from dashboard.run_daily import add_gpu_history


class PriceFreshnessTests(unittest.TestCase):
    def test_independent_retail_quote_is_not_substituted_for_street_average(self):
        raw = b'''<script type="application/ld+json">{"@type":"Product","sku":"MZ-V9P1T0B/AM","size":"1 TB","offers":{"priceCurrency":"USD","price":"319.99","availability":"https://schema.org/OutOfStock"}}</script>'''
        row = parse_samsung_ssd(raw, "2026-11-13")[0]
        self.assertEqual(row["category"], "SSD official retail")
        self.assertEqual(row["price"], 319.99)
        self.assertIn("OutOfStock", row["availability"])
        self.assertIsNone(row["as_of"])
        with self.assertRaises(ValueError):
            parse_samsung_ssd(raw.replace(b'1 TB', b'2 TB'), "2026-11-13")

    def test_flat_median_does_not_hide_individual_regional_quote_changes(self):
        def quote(region, price):
            return {"provider": "Azure", "gpu": "H100", "sku": "same", "region": region,
                    "billing": "Spot", "gpu_count": 1, "usd_per_gpu_hour": price}
        previous = {"snapshot_date": "2026-11-12", "rows": [quote("a", 1), quote("b", 3), quote("c", 5)]}
        current = {"rows": [quote("a", 2), quote("b", 3), quote("c", 4)]}
        add_gpu_history(current, previous, "2026-11-13")
        self.assertEqual(current["quote_change_summary"]["changed_quotes"], 2)
        self.assertEqual(current["price_history"]["Azure|H100|Spot"][-1]["median"], 3)

    def test_network_failure_in_strict_mode_does_not_return_old_price(self):
        with tempfile.TemporaryDirectory() as directory:
            body = Path(directory) / "body"
            body.write_bytes(b"old price")
            with patch("dashboard.common._cache_paths", return_value=(body, Path(directory) / "meta")), patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
                with self.assertRaises(RuntimeError):
                    request_bytes("https://example.com", cache_key="test", retries=1, allow_stale_cache=False)
                self.assertEqual(request_bytes("https://example.com", cache_key="test", retries=1), b"old price")

    def test_section_dates_are_not_replaced_with_observation_day(self):
        html = b'''<table><tr><td><span class="tab_time">Last Update: Nov.2 2026 14:40 (GMT+8)</span></td></tr></table>
        <table><tr><td>DDR5 UDIMM 16GB</td><td>10</td><td>8</td><td>10</td><td>8</td><td>9</td><td>0.1%</td></tr></table>
        <span class="tab_time">LastUpdate:Oct.30 2026 11:30, (GMT+8)</span>
        <table><tr><td>Samsung</td><td>PCIe 4.0 X4</td><td>990 Pro</td><td>2 TB</td><td>300</td><td>250</td><td>280</td></tr></table>'''
        rows = parse_dramexchange(html, "2026-11-13")
        self.assertEqual(rows[0]["as_of"], "2026-11-02")
        self.assertEqual(rows[0]["unit"], "per module")
        self.assertEqual(rows[1]["as_of"], "2026-10-30")
        self.assertTrue(all(row["observed_on"] == "2026-11-13" for row in rows))
        self.assertEqual(rows[1]["usd_per_tb"], 140)

    def test_unavailable_date_remains_unknown(self):
        rows = parse_dramexchange(b'<tr><td>DDR5 16Gb (2Gx8) 4800</td><td>9</td><td>7</td><td>9</td><td>7</td><td>8</td></tr>', "2026-11-13")
        self.assertIsNone(rows[0]["as_of"])

    def test_failed_source_retains_previous_row_without_appending_history(self):
        previous = {"rows": [{"id": "trendforce:test", "price": 9, "history": [{"date": "2026-11-12", "price": 9}]}]}
        with patch("dashboard.storage_market.request_bytes", side_effect=RuntimeError("offline")), patch("dashboard.storage_market.request_json", side_effect=RuntimeError("offline")):
            payload = collect_storage("2026-11-13", previous=previous)
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["rows"][0]["status"], "stale")
        self.assertEqual(len(payload["rows"][0]["history"]), 1)

    def test_empty_html_is_error_not_success(self):
        with patch("dashboard.storage_market.request_bytes", return_value=b"<html>maintenance</html>"), patch("dashboard.storage_market.request_json", side_effect=RuntimeError("offline")):
            with self.assertRaises(ValueError):
                collect_storage("2026-11-13")

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from dashboard.prices import collect_gpu, parse_azure, parse_lambda_instances


ROOT = Path(__file__).resolve().parents[1]


class GpuCatalogTests(unittest.TestCase):
    def test_config_hardware_metadata_is_per_gpu(self):
        configs = json.loads((ROOT / "config/sources.json").read_text())["gpu_skus"]
        self.assertEqual(len(configs), 7)
        self.assertEqual({c["gpu"] for c in configs}, {"H100", "H100 NVL", "A100 80GB", "H200", "T4"})
        self.assertTrue(all(c["gpu_count"] > 0 and c["memory_gb"] > 0 and c["hardware_url"].startswith("https://learn.microsoft.com/") for c in configs))
        self.assertEqual(next(c for c in configs if c["sku"] == "Standard_NC80adis_H100_v5")["gpu_count"], 2)

    def test_azure_rejects_wrong_currency_and_sku(self):
        cfg = {"sku": "Standard_NC4as_T4_v3", "gpu": "T4", "gpu_count": 1, "memory_gb": 16, "gpu_class": "Inference"}
        base = {"productName": "Linux T4", "meterName": "T4", "type": "Consumption",
                "unitOfMeasure": "1 Hour", "isPrimaryMeterRegion": True, "tierMinimumUnits": 0,
                "retailPrice": 1, "meterId": "m", "armRegionName": "eastus", "currencyCode": "USD",
                "armSkuName": cfg["sku"]}
        rows = parse_azure([base, dict(base, currencyCode="EUR"), dict(base, armSkuName="other")], cfg)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["memory_gb"], 16)
        self.assertEqual(rows[0]["gpu_class"], "Inference")

    def test_zero_row_sku_marks_partial_and_failed_sku_keeps_other_prices(self):
        configs = [
            {"sku": "good", "gpu": "H100", "gpu_count": 1, "memory_gb": 80},
            {"sku": "empty", "gpu": "H200", "gpu_count": 8, "memory_gb": 141},
        ]
        def get(url, **kwargs):
            if "good" in url:
                return {"Items": [{"productName": "Linux H100", "meterName": "H100", "type": "Consumption",
                    "unitOfMeasure": "1 Hour", "isPrimaryMeterRegion": True, "tierMinimumUnits": 0,
                    "retailPrice": 2, "meterId": "m", "armRegionName": "eastus"}]}
            return {"Items": []}
        with patch("dashboard.prices.request_json", side_effect=get), patch("dashboard.prices.request_bytes", side_effect=RuntimeError("offline")), patch.dict("os.environ", {"RUNPOD_API_KEY": "", "VAST_API_KEY": ""}):
            result = collect_gpu("2026-11-13", configs)
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["status"], "partial")
        self.assertEqual([s["status"] for s in result["sources"][:2]], ["ok", "empty"])

    def test_lambda_single_gpu_table_keeps_vram_separate_from_vm_ram(self):
        header = "<tr><th>Plan</th><th>VRAM/GPU</th><th>vCPUs</th><th>RAM</th><th>STORAGE</th><th>PRICE/GPU/HR*</th></tr>"
        table = "<table>" + header + "<tr><td>NVIDIA H100 SXM</td><td>80 GB</td><td>26</td><td>225 GiB</td><td>2.75 TiB SSD</td><td>$4.89</td></tr></table>"
        html = ('<button role="tab" id="multi">8x</button><button role="tab" id="single">1x</button>'
                '<div role="tabpanel" aria-labelledby="single">' + table + '</div>'
                '<div role="tabpanel" aria-labelledby="multi">' + table + '</div>')
        rows = parse_lambda_instances(html, "2026-11-16", "2026-11-16T00:00:00+00:00")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["memory_gb"], 80)
        self.assertEqual(rows[0]["gpu_count"], 1)
        self.assertEqual(rows[0]["instance_usd_hour"], 4.89)
        self.assertIn("CPU/RAM/storage included", rows[0]["price_basis"])
        with self.assertRaisesRegex(ValueError, "未来生效"):
            parse_lambda_instances(html + "<p>These prices take effect November 16, 2026, at 00:00 UTC.</p>", "2026-11-13", "2026-11-13T00:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "未来生效"):
            parse_lambda_instances(html + "<p>These prices take effect November 16, 2026, at 00:00 UTC.</p>", "2026-11-16", "2026-11-15T23:59:59+00:00")
        with self.assertRaisesRegex(ValueError, "1x"):
            parse_lambda_instances('<button role="tab" id="multi">8x</button><div role="tabpanel" aria-labelledby="multi">' + table + "</div>", "2026-11-16", "2026-11-16T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import weekly_dashboard as WEEKLY
import github_collector as GITHUB_COLLECTOR
import github_dashboard as GITHUB_DASHBOARD


def model(model_id: str, downloads: int, *, pipeline: str = "text-generation", likes: int = 1, trend: float = 1) -> dict[str, str]:
    return {
        "snapshot_date": "", "id": model_id, "downloads_all_time": str(downloads), "downloads_30d": "100",
        "likes": str(likes), "trending_score": str(trend), "pipeline_tag": pipeline, "library_name": "transformers", "tags": "[]",
    }


def snapshot(day: date, rows: dict[str, dict[str, str]]) -> object:
    for row in rows.values():
        row["snapshot_date"] = day.isoformat()
    return WEEKLY.Snapshot(day, f"{day.isoformat()}T00:00:00+00:00", {"sha256": "test"}, rows)


class WeeklyDashboardTests(unittest.TestCase):
    def test_github_snapshot_parser_and_payload_contract(self):
        page = '<article class="Box-row"><h2><a href="/owner/repo">owner/repo</a></h2><p>Agent toolkit</p><span itemprop="programmingLanguage">Python</span><a href="/owner/repo/stargazers">1,234</a><span>567 stars this week</span></article>'
        rows = GITHUB_COLLECTOR.parse_trending(page, "https://github.com/trending?since=weekly", "2026-09-28T00:00:00Z")
        rows[0].update({"stars": 1234, "forks": 3, "topics": ["agent"], "domain": "AI Agent", "description_raw": "Agent toolkit", "use_case_zh": "主要用于AI Agent；仓库简介：Agent toolkit"})
        payload = GITHUB_DASHBOARD.build_payload({"dataset": "github_trending_weekly", "snapshot_date": "2026-09-28", "captured_at_utc": "2026-09-28T00:00:00Z", "generated_at_utc": "2026-09-28T00:00:00Z", "source": "test", "rows": rows})
        GITHUB_DASHBOARD.validate(payload)
        self.assertEqual(payload["count"], 1)
        self.assertIn("AI Agent", payload["rows"][0]["use_case_zh"])

    def test_deltas_are_normalized_and_ranked(self):
        earlier = snapshot(date(2026, 7, 1), {"org/a": model("org/a", 100)})
        previous = snapshot(date(2026, 7, 15), {"org/a": model("org/a", 1_500)})
        latest = snapshot(date(2026, 7, 23), {"org/a": model("org/a", 2_300)})
        result = WEEKLY.compute_weekly(latest, previous, earlier)
        row = result["rows"][0]
        self.assertEqual((row["downloads_this_period"], row["downloads_last_period"], row["download_acceleration"]), (700, 700, 0))
        self.assertEqual(row["rank"], 1)
        self.assertIn("折算为7日", row["download_note"])

    def test_new_models_watch_and_decreasing_totals_are_excluded(self):
        earlier = snapshot(date(2026, 7, 1), {"bad/model": model("bad/model", 2_000)})
        previous = snapshot(date(2026, 7, 8), {"bad/model": model("bad/model", 1_900)})
        latest = snapshot(date(2026, 7, 15), {
            "bad/model": model("bad/model", 2_100), "new/model": model("new/model", 50, trend=99),
        })
        result = WEEKLY.compute_weekly(latest, previous, earlier)
        self.assertEqual((result["invalid_count"], result["exact_count"], result["watch_count"]), (1, 0, 1))
        self.assertEqual(result["rows"][0]["model_url"], "https://huggingface.co/new/model")

    def test_limits_are_450_exact_plus_50_watch(self):
        earlier, previous, latest = {}, {}, {}
        for i in range(600):
            key = f"exact/{i}"
            earlier[key], previous[key], latest[key] = model(key, 1), model(key, 2), model(key, 3 + i)
        for i in range(100):
            key = f"watch/{i}"
            latest[key] = model(key, 1, trend=i)
        result = WEEKLY.compute_weekly(snapshot(date(2026, 7, 15), latest), snapshot(date(2026, 7, 8), previous), snapshot(date(2026, 7, 1), earlier))
        self.assertEqual((result["exact_count"], result["watch_count"], len(result["rows"])), (450, 50, 500))

    def test_duplicate_snapshot_rows_and_bad_checksums_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            data_path, manifest_path = directory / "models_20260701.csv.gz", directory / "manifest_20260701.json"
            fields = list(WEEKLY.REQUIRED_FIELDS)
            row = model("org/a", 1)
            row["snapshot_date"] = "2026-07-01"
            with gzip.open(data_path, "wt", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader(); writer.writerow(row); writer.writerow(row)
            manifest_path.write_text(json.dumps({"sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(), "row_count": 2}), encoding="utf-8")
            ref = WEEKLY.SnapshotRef(date(2026, 7, 1), data_path, manifest_path)
            with self.assertRaises(RuntimeError):
                WEEKLY.load_snapshot(ref)
            manifest_path.write_text(json.dumps({"sha256": "0" * 64, "row_count": 2}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                WEEKLY.load_snapshot(ref)

    def test_payload_contract(self):
        earlier = snapshot(date(2026, 7, 1), {"org/a": model("org/a", 1)})
        previous = snapshot(date(2026, 7, 8), {"org/a": model("org/a", 2)})
        latest = snapshot(date(2026, 7, 15), {"org/a": model("org/a", 3)})
        payload = WEEKLY.build_payload([latest, previous, earlier])
        WEEKLY.validate_payload(payload)
        self.assertEqual(payload["snapshot_dates"], ["2026-07-01", "2026-07-08", "2026-07-15"])
        self.assertEqual(payload["rows"][0]["task_type"], "LLM / Text Generation")


if __name__ == "__main__":
    unittest.main()

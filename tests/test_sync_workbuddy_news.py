import json
import tempfile
import unittest
from pathlib import Path

from scripts.sync_workbuddy_news import sync


class WorkBuddySyncTests(unittest.TestCase):
    def test_sync_copies_board_reports_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            destination = root / "destination"
            (source / "reports").mkdir(parents=True)
            (source / "index.html").write_text("<a href='reports/day.html'>day</a>", encoding="utf-8")
            (source / "reports/day.html").write_text("<h1>day</h1>", encoding="utf-8")

            manifest = sync(source, destination)

            self.assertEqual(manifest["dataset"], "workbuddy_ai_news_board")
            self.assertEqual(manifest["report_count"], 1)
            self.assertTrue((destination / "index.html").is_file())
            self.assertTrue((destination / "reports/day.html").is_file())
            self.assertEqual(json.loads((destination / "manifest.json").read_text())["report_count"], 1)


if __name__ == "__main__":
    unittest.main()

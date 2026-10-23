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
            (source / "index.html").write_text(
                '<html><head></head><body><div class="wrap"><div class="notice">remove me</div>'
                "<a href='reports/day.html'>day</a></div></body></html>",
                encoding="utf-8",
            )
            (source / "reports/day.html").write_text(
                '<html><head></head><body><div class="wrap"><h1>day</h1></div></body></html>',
                encoding="utf-8",
            )

            manifest = sync(source, destination)

            self.assertEqual(manifest["dataset"], "workbuddy_ai_news_board")
            self.assertEqual(manifest["report_count"], 1)
            self.assertTrue((destination / "index.html").is_file())
            self.assertTrue((destination / "reports/day.html").is_file())
            self.assertEqual(json.loads((destination / "manifest.json").read_text())["report_count"], 1)
            board_html = (destination / "index.html").read_text(encoding="utf-8")
            report_html = (destination / "reports/day.html").read_text(encoding="utf-8")
            self.assertNotIn("remove me", board_html)
            self.assertIn("← 返回总览", board_html)
            self.assertIn("← 返回 AI 新闻日报", report_html)
            first_manifest = (destination / "manifest.json").read_bytes()

            sync(source, destination)

            self.assertEqual((destination / "manifest.json").read_bytes(), first_manifest)

            (source / "reports/next-day.html").write_text("<h1>next day</h1>", encoding="utf-8")
            updated_manifest = sync(source, destination)
            self.assertEqual(updated_manifest["report_count"], 2)
            self.assertNotEqual((destination / "manifest.json").read_bytes(), first_manifest)


if __name__ == "__main__":
    unittest.main()

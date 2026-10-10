import json
import tempfile
import unittest
from pathlib import Path

from dashboard.x_watch import load_watchlist


class XWatchlistTests(unittest.TestCase):
    def test_project_watchlist_has_expected_accounts_and_priority_subset(self):
        accounts = load_watchlist()
        self.assertEqual(len(accounts), 50)
        self.assertEqual(len({item["handle"].lower() for item in accounts}), 50)
        self.assertEqual(sum(item["priority"] for item in accounts), 15)
        tibo = next(item for item in accounts if item["handle"] == "thsottiaux")
        self.assertEqual(tibo["name"], "Tibo")
        self.assertIn("Codex", tibo["focus"])

    def test_invalid_or_duplicate_handles_are_rejected(self):
        for accounts in (
            [{"handle": "bad-handle"}],
            [{"handle": "OpenAI"}, {"handle": "openai"}],
        ):
            with self.subTest(accounts=accounts), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "watchlist.json"
                path.write_text(json.dumps({"accounts": accounts}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_watchlist(path)


if __name__ == "__main__":
    unittest.main()

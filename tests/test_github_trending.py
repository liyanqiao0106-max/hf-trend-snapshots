import unittest
from unittest.mock import patch

from dashboard.github_trending import collect_github_trending
from github_collector import parse_trending


def page(period: str, *, description: str = "General purpose tool", stars: str = "1,234", growth: str = "56") -> str:
    label = {"daily": "today", "weekly": "this week", "monthly": "this month"}[period]
    return (f'<article class="Box-row"><h2><a href="/owner/repo">owner/repo</a></h2>'
            f'<p>{description}</p><a href="/owner/repo/stargazers">{stars}</a>'
            f'<span>{growth} stars {label}</span></article>')


class GitHubTrendingTests(unittest.TestCase):
    def test_period_stars_are_taken_from_matching_source_page(self):
        for period in ("daily", "weekly", "monthly"):
            with self.subTest(period=period):
                rows = parse_trending(page(period), f"https://github.com/trending?since={period}", "2026-10-29T00:00:00Z")
                self.assertEqual(rows[0]["stars_in_period"], 56)
                self.assertEqual(rows[0]["page_stars"], 1234)
                self.assertEqual(rows[0]["stars_this_week"], 56 if period == "weekly" else None)

    def test_three_periods_keep_full_site_rows_and_original_description(self):
        pages = {period: page(period, description="General purpose tool") for period in ("daily", "weekly", "monthly")}
        with patch("dashboard.github_trending.request_text", side_effect=lambda url: pages[url.split("=")[-1]]):
            payload = collect_github_trending("2026-10-29")
        self.assertEqual(payload["dataset"], "github_trending_all")
        self.assertEqual(len(payload["rows"]), 3)
        self.assertEqual([row["period"] for row in payload["rows"]], ["daily", "weekly", "monthly"])
        self.assertTrue(all(row["description_raw"] == "General purpose tool" for row in payload["rows"]))
        self.assertEqual(len(payload["sources"]), 3)
        self.assertIn("captured_at_utc", payload)

    def test_missing_period_stars_fails_whole_snapshot(self):
        pages = {period: page(period, growth="") for period in ("daily", "weekly", "monthly")}
        with patch("dashboard.github_trending.request_text", side_effect=lambda url: pages[url.split("=")[-1]]):
            with self.assertRaisesRegex(ValueError, "缺少 Stars 数据"):
                collect_github_trending("2026-10-29")


if __name__ == "__main__":
    unittest.main()

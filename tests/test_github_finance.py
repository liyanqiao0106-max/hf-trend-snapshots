import unittest
from unittest.mock import patch

from dashboard.github_finance import collect_github_finance


class FinanceTests(unittest.TestCase):
    def test_deduplication_comparison_and_skill_verification(self):
        def fake_request(url, token):
            if '/search/repositories?' in url:
                return {'items': [{'full_name': 'org/tool', 'html_url': 'https://github.com/org/tool', 'stargazers_count': 120, 'default_branch': 'main', 'description': 'Finance research'}]}
            return {'tree': [{'type': 'blob', 'path': 'skills/research/SKILL.md'}], 'truncated': False}
        with patch('dashboard.github_finance.request_json', side_effect=fake_request):
            data = collect_github_finance('2026-11-12', {'snapshot_date': '2026-11-05', 'rows': [{'full_name': 'org/tool', 'stars': 100}]})
        self.assertEqual(len(data['rows']), 1)
        self.assertEqual(data['rows'][0]['stars_net_change'], 20)
        self.assertEqual(data['rows'][0]['skill_status'], 'verified')
        self.assertEqual(data['comparison_snapshot_date'], '2026-11-05')

    def test_search_failure_never_fabricates_empty_success(self):
        with patch('dashboard.github_finance.request_json', side_effect=OSError('offline')):
            with self.assertRaises(ValueError):
                collect_github_finance('2026-11-12')

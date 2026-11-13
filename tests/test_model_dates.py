import unittest

from dashboard.usage import model_metadata


class ModelDatesTests(unittest.TestCase):
    def test_retains_first_observation_as_window_rolls_and_does_not_parse_id(self):
        model = "openai/example-20261101"
        previous = {"model_metadata": {model: {"first_seen_week": "2026-10-05"}}}
        rows = [{"week_start": "2026-11-09", "top_models": [{"id": model}]}]
        metadata = model_metadata(rows, previous)
        self.assertEqual(metadata[model]["first_seen_week"], "2026-10-05")
        self.assertIsNone(metadata[model]["release_date"])

    def test_official_release_evidence_rejects_third_party_and_future_dates(self):
        rows = [{"week_start": "2026-11-09", "top_models": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}]
        releases = {
            "a": {"release_date": "2026-11-01", "source_url": "https://openai.com/index/example/"},
            "b": {"release_date": "2026-11-01", "source_url": "https://example.com/release"},
            "c": {"release_date": "2027-01-01", "source_url": "https://openai.com/index/future/"},
        }
        metadata = model_metadata(rows, releases=releases, as_of="2026-11-13")
        self.assertEqual(metadata["a"]["date_basis"], "official_release")
        self.assertIsNone(metadata["b"]["release_date"])
        self.assertIsNone(metadata["c"]["release_date"])

    def test_old_snapshot_history_is_used_for_earliest_week(self):
        rows = [{"week_start": "2026-11-09", "top_models": [{"id": "a"}]}]
        old = {"rows": [{"week_start": "2026-09-07", "top_models": [{"id": "a"}]}]}
        self.assertEqual(model_metadata(rows, old)["a"]["first_seen_week"], "2026-09-07")

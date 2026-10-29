from __future__ import annotations

import unittest
from unittest.mock import patch

from dashboard.hf_cards import MISSING, card_excerpt, enrich_rows


class ModelCardTests(unittest.TestCase):
    def test_excerpt_skips_metadata_and_uses_actual_card_prose(self):
        card = """---
license: apache-2.0
---
# Example

This model was trained for passage ranking.

It can be used to sort retrieved passages for a search query.
"""
        self.assertEqual(card_excerpt(card), "This model was trained for passage ranking. It can be used to sort retrieved passages for a search query.")

    def test_missing_card_does_not_fall_back_to_download_claims(self):
        rows = [{"id": "org/model", "model_url": "https://huggingface.co/org/model", "download_note": "下载增长"}]
        with patch("dashboard.hf_cards.fetch_card", return_value=(None, "missing_card")):
            enrich_rows(rows, None, "2026-10-29", workers=1)
        self.assertEqual(rows[0]["model_description"], MISSING)
        self.assertEqual(rows[0]["model_description_status"], "missing_card")

    def test_recent_verified_card_is_reused(self):
        rows = [{"id": "org/model", "model_url": "https://huggingface.co/org/model"}]
        previous = {"rows": [{"id": "org/model", "model_description": "A search reranking model.", "model_description_status": "verified", "model_card_checked_at": "2026-10-20"}]}
        with patch("dashboard.hf_cards.fetch_card") as fetch:
            enrich_rows(rows, previous, "2026-10-29", workers=1)
        fetch.assert_not_called()
        self.assertEqual(rows[0]["model_description"], "A search reranking model.")


if __name__ == "__main__":
    unittest.main()

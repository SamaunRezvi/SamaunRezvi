"""Tests for the small helpers in card_kit."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

import card_kit  # noqa: E402


class MetricsTests(unittest.TestCase):
    def test_both_fonts_have_a_width_table(self):
        table = card_kit.metrics()
        self.assertIn(card_kit.TITLE_FONT[0], table)
        self.assertIn(card_kit.BODY_FONT[0], table)

    def test_font_files_exist(self):
        for _, _, filename in (card_kit.TITLE_FONT, card_kit.BODY_FONT):
            self.assertTrue(os.path.exists(os.path.join(card_kit.FONT_DIR, filename)), filename)


class TextWidthTests(unittest.TestCase):
    family = card_kit.BODY_FONT[0]

    def test_unknown_character_counts_as_055_em(self):
        self.assertAlmostEqual(card_kit.text_width("\U0010FFFF", self.family, 20), 11.0)

    def test_empty_text_has_no_width(self):
        self.assertEqual(card_kit.text_width("", self.family, 20), 0)

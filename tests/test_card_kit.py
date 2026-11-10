"""Tests for the SVG card renderer."""
import base64
import json
import os
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

import card_kit  # noqa: E402

SPEC = {
    "accent": "#58A6FF",
    "eyebrow": "Principle 01",
    "number": "01",
    "title": "Missing data & more",
    "code": "renderQualityState()",
    "body": "If a sensor has not reported, the interface says so. It never renders a zero.",
}
PIXEL = "data:image/svg+xml;base64," + base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg'/>").decode()


class FontTests(unittest.TestCase):
    def test_font_files_exist(self):
        for _, _, filename in (card_kit.TITLE_FONT, card_kit.BODY_FONT):
            self.assertTrue(os.path.exists(os.path.join(card_kit.FONT_DIR, filename)), filename)

    def test_metrics_cover_both_fonts_and_basic_letters(self):
        for family in (card_kit.TITLE_FONT[0], card_kit.BODY_FONT[0]):
            table = card_kit.metrics()[family]
            for char in "aeiouAZ09 .,":
                self.assertIn(char, table, (family, char))

    def test_metrics_file_is_valid_json(self):
        with open(os.path.join(card_kit.FONT_DIR, "metrics.json"), encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)), 2)


class WrapTests(unittest.TestCase):
    family = card_kit.BODY_FONT[0]

    def test_lines_fit_the_width(self):
        text = "word " * 60
        for line in card_kit.wrap(text, self.family, 14.5, 300):
            self.assertLessEqual(card_kit.text_width(line, self.family, 14.5), 300)

    def test_no_words_are_lost(self):
        text = "alpha beta gamma delta epsilon zeta eta theta"
        lines = card_kit.wrap(text, self.family, 14.5, 120)
        self.assertEqual(" ".join(lines).split(), text.split())

    def test_empty_text_gives_no_lines(self):
        self.assertEqual(card_kit.wrap("", self.family, 14.5, 300), [])

    def test_a_single_long_word_is_kept_on_its_own_line(self):
        self.assertEqual(card_kit.wrap("x" * 80, self.family, 14.5, 100), ["x" * 80])

    def test_wider_text_measures_wider(self):
        self.assertGreater(card_kit.text_width("abcdef", self.family, 14), card_kit.text_width("abc", self.family, 14))

    def test_unknown_characters_use_a_default_width(self):
        self.assertGreater(card_kit.text_width("\u4e2d", self.family, 10), 0)


class RenderTests(unittest.TestCase):
    def test_output_is_well_formed_xml(self):
        ET.fromstring(card_kit.render(SPEC))

    def test_text_is_escaped(self):
        self.assertIn("Missing data &amp; more", card_kit.render(SPEC))

    def test_embeds_both_fonts(self):
        svg = card_kit.render(SPEC)
        self.assertEqual(svg.count("@font-face"), 2)

    def test_footer_is_optional(self):
        plain = card_kit.natural_height(SPEC)
        with_footer = card_kit.natural_height(dict(SPEC, footer_left="Updated Nov 5, 2026", footer_right="Source code \u2192"))
        self.assertGreater(with_footer, plain)

    def test_chips_and_badges_are_drawn(self):
        svg = card_kit.render(dict(SPEC, chips=["TypeScript", "nextjs"], badges=[(PIXEL, 60, 20)]))
        self.assertIn("TypeScript", svg)
        self.assertIn("<image", svg)

    def test_many_chips_wrap_onto_more_rows(self):
        few = card_kit.natural_height(dict(SPEC, chips=["a", "b"]))
        many = card_kit.natural_height(dict(SPEC, chips=[f"technology{i}" for i in range(12)]))
        self.assertGreater(many, few)

    def test_minimum_height_is_respected(self):
        self.assertEqual(card_kit.layout(SPEC, min_height=500)[1], 500)

    def test_equalise_gives_each_row_one_height(self):
        short = dict(SPEC, body="Short.")
        specs = [SPEC, short, short, short]
        heights = [ET.fromstring(svg).get("height") for svg in card_kit.equalise(specs)]
        self.assertEqual(heights[0], heights[1])
        self.assertEqual(heights[2], heights[3])
        self.assertNotEqual(heights[0], heights[2])

    def test_lighten_mixes_towards_white(self):
        self.assertEqual(card_kit.lighten("#000000", 1.0), "#FFFFFF")
        self.assertEqual(card_kit.lighten("#112233", 0.0), "#112233")

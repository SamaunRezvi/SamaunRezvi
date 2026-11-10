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


class WidthAndStatTests(unittest.TestCase):
    def test_cards_can_use_a_custom_width(self):
        root = ET.fromstring(card_kit.render(dict(SPEC, width=270)))
        self.assertEqual(root.get("width"), "270")

    def test_narrow_cards_wrap_text_into_more_lines(self):
        wide = card_kit.natural_height(SPEC)
        narrow = card_kit.natural_height(dict(SPEC, width=240))
        self.assertGreater(narrow, wide)

    def test_title_size_changes_the_title_font(self):
        self.assertIn('font-size="20"', card_kit.render(dict(SPEC, title_size=20)))

    def test_stat_card_is_well_formed_and_small(self):
        spec = {"accent": "#58A6FF", "label": "Work", "number": "15+", "title": "Projects", "caption": "across web and data"}
        root = ET.fromstring(card_kit.render_stat(spec))
        self.assertEqual(root.get("width"), str(card_kit.STAT_WIDTH))
        self.assertLessEqual(card_kit.STAT_WIDTH, 180)

    def test_stat_card_shows_every_text(self):
        spec = {"accent": "#58A6FF", "label": "Work", "number": "15+", "title": "Projects", "caption": "across web & data"}
        svg = card_kit.render_stat(spec)
        for text in ("WORK", "15+", "PROJECTS", "across web &amp; data"):
            self.assertIn(text, svg)


HERO = {
    "avatar": PIXEL,
    "name": "Hi, I’m Samaun Rezvi",
    "taglines": ["Full-Stack Web Developer", "I build products end to end", "Frontend · Backend · Data · Deploy"],
    "education": "Computer Science & Engineering · Daffodil International University · DSC, Dhaka, Bangladesh",
    "roles": [(PIXEL, 100, 20), (PIXEL, 90, 20), (PIXEL, 95, 20)],
    "status": "status: open to opportunities · response time: usually within a day",
}


class HeroTests(unittest.TestCase):
    def test_hero_is_well_formed_and_has_the_expected_size(self):
        root = ET.fromstring(card_kit.render_hero(HERO))
        self.assertEqual((root.get("width"), root.get("height")), (str(card_kit.HERO_WIDTH), str(card_kit.HERO_HEIGHT + card_kit.HERO_GAP)))

    def test_hero_keeps_every_piece_of_text(self):
        svg = card_kit.render_hero(HERO)
        for text in HERO["taglines"] + [HERO["name"], HERO["status"]]:
            self.assertIn(text.replace("&", "&amp;"), svg)
        self.assertIn("Computer Science &amp; Engineering", svg)

    def test_hero_draws_the_avatar_and_role_badges(self):
        self.assertEqual(card_kit.render_hero(HERO).count("<image"), 4)

    def test_every_tagline_gets_its_own_animated_line(self):
        svg = card_kit.render_hero(HERO)
        for i in range(3):
            self.assertIn(f'class="t tag l{i}"', svg)
        self.assertIn("@keyframes cycle", svg)

    def test_reduced_motion_shows_only_the_first_tagline(self):
        self.assertIn("prefers-reduced-motion", card_kit.tagline_css(3))

    def test_tagline_animation_spans_all_lines(self):
        self.assertIn("animation:cycle 9s infinite", card_kit.tagline_css(3))
        self.assertIn("animation-delay:6s", card_kit.tagline_css(3))

    def test_wide_badge_rows_are_scaled_to_fit(self):
        wide = dict(HERO, roles=[(PIXEL, 400, 20)] * 3)
        root = ET.fromstring(card_kit.render_hero(wide))
        for image in root.iter("{http://www.w3.org/2000/svg}image"):
            self.assertLessEqual(float(image.get("x", 0)) + float(image.get("width")), card_kit.HERO_WIDTH + 0.5)

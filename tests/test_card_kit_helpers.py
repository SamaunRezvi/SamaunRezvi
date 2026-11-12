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

    def test_width_is_proportional_to_size(self):
        small = card_kit.text_width("Samaun", self.family, 10)
        large = card_kit.text_width("Samaun", self.family, 20)
        self.assertAlmostEqual(large, small * 2)

    def test_spacing_adds_per_character(self):
        base = card_kit.text_width("abc", self.family, 12)
        self.assertAlmostEqual(card_kit.text_width("abc", self.family, 12, spacing=1.5), base + 4.5)


class WrapTests(unittest.TestCase):
    family = card_kit.BODY_FONT[0]
    text = "A monitoring platform with no remote control over the hardware it observes"

    def test_no_line_is_wider_than_the_limit(self):
        for line in card_kit.wrap(self.text, self.family, 16, 220):
            self.assertLessEqual(card_kit.text_width(line, self.family, 16), 220)

    def test_no_word_is_lost_or_reordered(self):
        lines = card_kit.wrap(self.text, self.family, 16, 220)
        self.assertEqual(" ".join(lines).split(), self.text.split())

    def test_a_long_word_gets_its_own_line(self):
        self.assertEqual(card_kit.wrap("supercalifragilistic", self.family, 16, 20), ["supercalifragilistic"])


class LightenTests(unittest.TestCase):
    def test_zero_keeps_the_colour(self):
        self.assertEqual(card_kit.lighten("#58A6FF", 0), "#58A6FF")

    def test_one_gives_white(self):
        self.assertEqual(card_kit.lighten("#58A6FF", 1), "#FFFFFF")

    def test_every_accent_stays_a_hex_colour(self):
        for colour in card_kit.ACCENTS:
            self.assertRegex(card_kit.lighten(colour), r"^#[0-9A-F]{6}$")


class EqualiseTests(unittest.TestCase):
    def specs(self):
        base = {"accent": "#58A6FF", "eyebrow": "Principle", "number": "01", "code": "run()"}
        return [dict(base, title=f"Card {i}", body="word " * (10 + i * 25)) for i in range(4)]

    def test_returns_one_svg_per_spec(self):
        self.assertEqual(len(card_kit.equalise(self.specs())), 4)

    def test_titles_stay_in_order(self):
        svgs = card_kit.equalise(self.specs())
        for i, svg in enumerate(svgs):
            self.assertIn(f"Card {i}", svg)


class HeroEscapeTests(unittest.TestCase):
    def test_markup_in_the_name_is_escaped(self):
        import base64
        import xml.etree.ElementTree as ET
        pixel = "data:image/svg+xml;base64," + base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg'/>").decode()
        spec = {
            "avatar": pixel,
            "name": "<b>Name</b> & co",
            "taglines": ["One", "Two"],
            "education": "School",
            "roles": [(pixel, 90, 20)],
            "status": "ok",
        }
        svg = card_kit.render_hero(spec)
        ET.fromstring(svg)
        self.assertNotIn("<b>Name</b>", svg)
        self.assertIn("&lt;b&gt;Name&lt;/b&gt; &amp; co", svg)


class DeterminismTests(unittest.TestCase):
    spec = {"accent": "#58A6FF", "eyebrow": "Principle", "number": "01", "title": "Stable output", "code": "run()", "body": "Same input, same bytes."}

    def test_render_is_repeatable(self):
        self.assertEqual(card_kit.render(self.spec), card_kit.render(self.spec))

    def test_stat_render_is_repeatable(self):
        stat = {"accent": "#BC8CFF", "label": "Work", "number": "15+", "title": "Projects", "caption": "across web"}
        self.assertEqual(card_kit.render_stat(stat), card_kit.render_stat(stat))


class MinHeightTests(unittest.TestCase):
    spec = {"accent": "#58A6FF", "eyebrow": "Principle", "number": "01", "title": "Min height", "code": "run()", "body": "Short."}

    def test_natural_height_is_the_smallest_height(self):
        import xml.etree.ElementTree as ET
        natural = card_kit.natural_height(self.spec)
        for extra in (0, 40):
            root = ET.fromstring(card_kit.render(self.spec, min_height=natural + extra))
            self.assertEqual(int(float(root.get("height"))), natural + extra)

    def test_a_smaller_minimum_does_not_shrink_the_card(self):
        import xml.etree.ElementTree as ET
        natural = card_kit.natural_height(self.spec)
        root = ET.fromstring(card_kit.render(self.spec, min_height=10))
        self.assertEqual(int(float(root.get("height"))), natural)


class StatWidthTests(unittest.TestCase):
    def test_width_attribute_matches_the_constant(self):
        import xml.etree.ElementTree as ET
        stat = {"accent": "#F0883E", "label": "Work", "number": "15+", "title": "Projects", "caption": "across web"}
        root = ET.fromstring(card_kit.render_stat(stat))
        self.assertEqual(root.get("width"), str(card_kit.STAT_WIDTH))


class TaglineTimingTests(unittest.TestCase):
    def test_total_duration_is_lines_times_seconds(self):
        css = card_kit.tagline_css(4, seconds_each=2)
        self.assertIn("animation:cycle 8s infinite", css)
        self.assertIn("animation-delay:6s", css)

    def test_each_line_has_a_delay_rule(self):
        css = card_kit.tagline_css(3)
        for i in range(3):
            self.assertIn(f".l{i}", css)


class AccentPaletteTests(unittest.TestCase):
    def test_colours_are_unique_hex(self):
        import re
        self.assertEqual(len(card_kit.ACCENTS), len(set(card_kit.ACCENTS)))
        for colour in card_kit.ACCENTS:
            self.assertRegex(colour, r"^#[0-9A-F]{6}$")

    def test_no_accent_is_a_green(self):
        for colour in card_kit.ACCENTS:
            r, g, b = (int(colour[i : i + 2], 16) for i in (1, 3, 5))
            self.assertFalse(g > r + 40 and g > b + 40, colour)

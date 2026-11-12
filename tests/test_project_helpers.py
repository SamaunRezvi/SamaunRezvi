"""Tests for the small helpers in the card script."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

import generate_profile_cards as gen  # noqa: E402


class SlugTests(unittest.TestCase):
    def test_lowercases_and_replaces_spaces(self):
        self.assertEqual(gen.project_slug({"name": "My Cool App"}), "my-cool-app")

    def test_keeps_dots_dashes_and_underscores(self):
        self.assertEqual(gen.project_slug({"name": "a_b-c.d"}), "a_b-c.d")

    def test_trims_separators_at_the_ends(self):
        self.assertEqual(gen.project_slug({"name": "!!demo!!"}), "demo")


class LiveDemoTests(unittest.TestCase):
    def test_https_and_http_links_count(self):
        self.assertTrue(gen.has_live_demo({"homepageUrl": "https://demo.dev"}))
        self.assertTrue(gen.has_live_demo({"homepageUrl": " http://demo.dev"}))

    def test_missing_or_odd_values_do_not(self):
        self.assertFalse(gen.has_live_demo({}))
        self.assertFalse(gen.has_live_demo({"homepageUrl": None}))
        self.assertFalse(gen.has_live_demo({"homepageUrl": "ftp://files.dev"}))
        self.assertFalse(gen.has_live_demo({"homepageUrl": "demo.dev"}))


class ShortenTests(unittest.TestCase):
    def test_short_text_is_only_capitalised(self):
        self.assertEqual(gen.shorten("a small tool"), "A small tool")

    def test_long_text_ends_with_an_ellipsis_inside_the_limit(self):
        out = gen.shorten("word " * 80, limit=40)
        self.assertLessEqual(len(out), 40)
        self.assertTrue(out.endswith("\u2026"))

    def test_cut_happens_between_words(self):
        out = gen.shorten("alpha beta gamma delta", limit=14)
        self.assertEqual(out, "Alpha beta\u2026")


class LimitTests(unittest.TestCase):
    def test_description_limit_is_a_positive_number(self):
        self.assertGreater(gen.MAX_DESCRIPTION, 40)

    def test_history_page_limit_is_bounded(self):
        self.assertGreater(gen.MAX_HISTORY_PAGES, 0)
        self.assertLessEqual(gen.MAX_HISTORY_PAGES, 200)


class ColourConstantTests(unittest.TestCase):
    def test_named_colours_are_hex(self):
        import re
        names = [n for n in dir(gen) if n.isupper() and isinstance(getattr(gen, n), str) and getattr(gen, n).startswith("#")]
        self.assertTrue(names)
        for name in names:
            self.assertRegex(getattr(gen, name), r"^#[0-9A-Fa-f]{6}$", name)

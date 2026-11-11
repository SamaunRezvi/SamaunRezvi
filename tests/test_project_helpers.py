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

"""Unit tests for the SVG card builders in .github/scripts/generate_profile_cards.py."""
import math
import os
import sys
import types
import unittest
import xml.etree.ElementTree as ET

try:
    import requests  # noqa: F401
except ImportError:  # the builders under test never touch the network
    sys.modules["requests"] = types.ModuleType("requests")

os.environ.setdefault("GITHUB_TOKEN", "test-token")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".github", "scripts"))

import generate_profile_cards as cards  # noqa: E402

LANGS = [
    {"name": "TypeScript", "value": 60, "color": "#3178c6"},
    {"name": "Python", "value": 30, "color": "#3572A5"},
    {"name": "HTML", "value": 10, "color": "#e34c26"},
]
STATS = [
    ("STAR", "Total Stars:", "12"),
    ("COMMIT", "Total Commits:", "345"),
    ("PR", "Total PRs:", "6"),
]
STREAK = {
    "total": 607,
    "total_range": "Jan 1, 2020 - Present",
    "current": 4,
    "current_range": "Nov 4, 2026 - Nov 7, 2026",
    "longest": 21,
    "longest_range": "Mar 1, 2026 - Mar 21, 2026",
}
DAILY = [(d, d % 5) for d in range(1, 32)]


def parse(svg):
    return ET.fromstring(svg)


class ArcPathTests(unittest.TestCase):
    def test_path_starts_with_move_and_is_closed(self):
        d = cards.arc_path(0, 0, 10, 5, 0, math.pi / 2)
        self.assertTrue(d.startswith("M"))
        self.assertTrue(d.endswith("Z"))

    def test_starts_at_top_of_circle_for_zero_angle(self):
        d = cards.arc_path(0, 0, 10, 5, 0, math.pi / 2)
        self.assertTrue(d.startswith("M0.000,-10.000"))

    def test_small_sweep_uses_small_arc_flag(self):
        d = cards.arc_path(0, 0, 10, 5, 0, math.pi / 2)
        self.assertIn(" 0 0 1 ", d)

    def test_large_sweep_uses_large_arc_flag(self):
        d = cards.arc_path(0, 0, 10, 5, 0, math.pi * 1.5)
        self.assertIn(" 0 1 1 ", d)


class CardShellTests(unittest.TestCase):
    def test_title_is_xml_escaped(self):
        svg = cards.card_shell("A & B", 100, 50, "")
        self.assertIn("A &amp; B", svg)

    def test_declares_width_height_and_viewbox(self):
        svg = cards.card_shell("T", 340, 200, "")
        self.assertIn('width="340" height="200" viewBox="0 0 340 200"', svg)

    def test_body_is_included(self):
        svg = cards.card_shell("T", 100, 50, '<circle id="x"></circle>')
        self.assertIn('<circle id="x"></circle>', svg)

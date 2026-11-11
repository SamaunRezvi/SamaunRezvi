"""Tests for the generated README cards (Principles, Selected Work, stats, tech, quotes, contact)."""
import glob
import json
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import make_cards  # noqa: E402

with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
    README = f.read()
with open(make_cards.CONTENT, encoding="utf-8") as f:
    CONTENT = json.load(f)

COUNTS = {"principles": 4, "work": 6, "stats": 4, "tech": 5, "quotes": 5, "contact": 3}


class ContentTests(unittest.TestCase):
    def test_every_group_has_the_expected_number_of_cards(self):
        for key, count in COUNTS.items():
            self.assertEqual(len(CONTENT[key]), count, key)

    def test_every_badge_file_exists(self):
        files = [name for item in CONTENT["work"] for name in item["badges"]]
        files += [badge["file"] for item in CONTENT["tech"] for badge in item["badges"]]
        for name in files:
            self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "badges", name)), name)

    def test_humanize_formats_folder_names(self):
        self.assertEqual(make_cards.humanize("iot-monitoring/"), "IoT Monitoring")
        self.assertEqual(make_cards.humanize("design-systems/"), "Design Systems")

    def test_no_information_was_lost_from_the_original_sections(self):
        self.assertEqual([s["number"] for s in CONTENT["stats"]], ["15+", "10+", "2", "99.9%"])
        self.assertEqual([t["title"] for t in CONTENT["tech"]], ["Languages", "Frontend", "Backend-Data", "Architecture", "Tooling"])
        self.assertEqual(CONTENT["quotes"][0]["author"], "Edsger W. Dijkstra")
        self.assertEqual([c["title"] for c in CONTENT["contact"]], ["Full-time", "Freelance", "Collaboration"])


class GeneratedCardTests(unittest.TestCase):
    def test_every_card_file_exists_and_is_well_formed(self):
        for prefix, key, *_ in make_cards.GROUPS:
            for i in range(len(CONTENT[key])):
                path = os.path.join(ROOT, "assets", "cards", f"{prefix}-{i + 1}.svg")
                with open(path, encoding="utf-8") as f:
                    ET.fromstring(f.read())

    def test_no_stale_card_files(self):
        expected = sum(len(CONTENT[key]) for _, key, *_ in make_cards.GROUPS)
        self.assertEqual(len(glob.glob(os.path.join(ROOT, "assets", "cards", "*.svg"))), expected)

    def test_work_and_tech_cards_embed_their_badges(self):
        for prefix, expected in (("work-1", 3), ("tech-1", 6)):
            with open(os.path.join(ROOT, "assets", "cards", f"{prefix}.svg"), encoding="utf-8") as f:
                self.assertEqual(f.read().count("<image"), expected, prefix)

    def test_readme_markers_appear_once_each(self):
        for key in COUNTS:
            self.assertEqual(README.count(f"<!-- CARDS:{key}:START -->"), 1, key)
            self.assertEqual(README.count(f"<!-- CARDS:{key}:END -->"), 1, key)

    def test_readme_shows_every_card_with_alt_text(self):
        for prefix, key, *_ in make_cards.GROUPS:
            for i in range(len(CONTENT[key])):
                match = re.search(rf'<img alt="([^"]+)" src="assets/cards/{prefix}-{i + 1}\.svg"', README)
                self.assertIsNotNone(match, f"{prefix}-{i + 1}")

    def test_replace_block_keeps_the_surrounding_text(self):
        text = "a\n<!-- CARDS:x:START -->\nold\n<!-- CARDS:x:END -->\nb"
        self.assertEqual(
            make_cards.replace_block(text, "x", "new"),
            "a\n<!-- CARDS:x:START -->\nnew\n<!-- CARDS:x:END -->\nb",
        )


class AccentTests(unittest.TestCase):
    def test_accent_cycles_through_the_palette(self):
        import make_cards
        palette = make_cards.card_kit.ACCENTS
        self.assertEqual(make_cards.accent(0), palette[0])
        self.assertEqual(make_cards.accent(len(palette)), palette[0])
        self.assertEqual(make_cards.accent(len(palette) + 2), palette[2])

    def test_humanize_keeps_known_acronyms_upper_case(self):
        import make_cards
        self.assertEqual(make_cards.humanize("ui-ux-api/"), "UI UX API")


class MissingMarkerTests(unittest.TestCase):
    def test_missing_markers_raise(self):
        import make_cards
        with self.assertRaises(ValueError):
            make_cards.replace_block("no markers here", "work", "<p></p>")

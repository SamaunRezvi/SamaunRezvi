"""Tests for the generated Principles and Selected Work cards."""
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


class ContentTests(unittest.TestCase):
    def test_has_four_principles_and_six_projects(self):
        self.assertEqual(len(CONTENT["principles"]), 4)
        self.assertEqual(len(CONTENT["work"]), 6)

    def test_every_badge_file_exists(self):
        for item in CONTENT["work"]:
            for name in item["badges"]:
                self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "badges", name)), name)

    def test_humanize_formats_folder_names(self):
        self.assertEqual(make_cards.humanize("iot-monitoring/"), "IoT Monitoring")
        self.assertEqual(make_cards.humanize("design-systems/"), "Design Systems")


class GeneratedCardTests(unittest.TestCase):
    def test_every_card_file_exists_and_is_well_formed(self):
        for prefix, key in (("principle", "principles"), ("work", "work")):
            for i in range(len(CONTENT[key])):
                path = os.path.join(ROOT, "assets", "cards", f"{prefix}-{i + 1}.svg")
                with open(path, encoding="utf-8") as f:
                    ET.fromstring(f.read())

    def test_no_stale_card_files(self):
        expected = len(CONTENT["principles"]) + len(CONTENT["work"])
        self.assertEqual(len(glob.glob(os.path.join(ROOT, "assets", "cards", "*.svg"))), expected)

    def test_work_cards_embed_their_tech_badges(self):
        with open(os.path.join(ROOT, "assets", "cards", "work-1.svg"), encoding="utf-8") as f:
            self.assertEqual(f.read().count("<image"), 3)

    def test_readme_markers_appear_once_each(self):
        for name in ("principles", "work"):
            self.assertEqual(README.count(f"<!-- CARDS:{name}:START -->"), 1)
            self.assertEqual(README.count(f"<!-- CARDS:{name}:END -->"), 1)

    def test_readme_shows_every_card_with_alt_text(self):
        for prefix, key in (("principle", "principles"), ("work", "work")):
            for i in range(len(CONTENT[key])):
                match = re.search(rf'<img alt="([^"]+)" src="assets/cards/{prefix}-{i + 1}\.svg"', README)
                self.assertIsNotNone(match, f"{prefix}-{i + 1}")

    def test_replace_block_keeps_the_surrounding_text(self):
        text = "a\n<!-- CARDS:x:START -->\nold\n<!-- CARDS:x:END -->\nb"
        self.assertEqual(
            make_cards.replace_block(text, "x", "new"),
            "a\n<!-- CARDS:x:START -->\nnew\n<!-- CARDS:x:END -->\nb",
        )

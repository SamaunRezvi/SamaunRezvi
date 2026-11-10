"""Tests for the serif heading images."""
import glob
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import make_headings  # noqa: E402

with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
    README = f.read()


class BuildSvgTests(unittest.TestCase):
    def build(self, text="Tech & Tools", bar=True):
        return make_headings.build_svg(text, 32, 760, "middle", bar, "#ffffff", "")

    def test_output_is_well_formed_xml(self):
        ET.fromstring(self.build())

    def test_text_is_escaped(self):
        self.assertIn("Tech &amp; Tools", self.build())

    def test_has_an_accessible_label(self):
        self.assertIn('aria-label="Tech &amp; Tools"', self.build())

    def test_accent_bar_is_optional(self):
        self.assertIn("linearGradient", self.build(bar=True))
        self.assertNotIn("linearGradient", self.build(bar=False))

    def test_uses_lining_numbers(self):
        self.assertIn("lining-nums", self.build("99.9%"))


class GeneratedHeadingTests(unittest.TestCase):
    def test_every_heading_has_dark_and_light_files(self):
        for slug, *_ in make_headings.HEADINGS:
            for theme in make_headings.THEMES:
                path = os.path.join(ROOT, "assets", "headings", f"{slug}-{theme}.svg")
                self.assertTrue(os.path.exists(path), path)

    def test_generated_files_embed_the_font_and_parse(self):
        for path in glob.glob(os.path.join(ROOT, "assets", "headings", "*.svg")):
            with open(path, encoding="utf-8") as f:
                text = f.read()
            ET.fromstring(text)
            self.assertIn("@font-face", text, path)
            self.assertIn("base64", text, path)

    def test_readme_uses_every_heading_in_both_themes(self):
        for slug, *_ in make_headings.HEADINGS:
            self.assertIn(f"assets/headings/{slug}-dark.svg", README, slug)
            self.assertIn(f"assets/headings/{slug}-light.svg", README, slug)

    def test_readme_picture_sources_exist(self):
        for source in re.findall(r'srcset="(assets/[^"]+)"', README):
            self.assertTrue(os.path.exists(os.path.join(ROOT, source)), source)

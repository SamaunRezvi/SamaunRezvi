"""Audit guards so the README stays readable on phones, tablets and desktops.

GitHub cannot run CSS media queries in a README. Two rules make the layout adapt:
images get a fixed pixel width (GitHub shrinks them to the screen width, so
side-by-side images stack on a phone), and nothing uses a fixed height or a small
percentage width, which would squash or shrink text on narrow screens.
"""
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
    README = f.read()

IMG_TAGS = re.findall(r"<img\b[^>]*>", README)
CARD_WIDTHS = {"420", "270", "168"}


def attribute(tag, name):
    match = re.search(rf'\s{name}="([^"]*)"', tag)
    return match.group(1) if match else None


def svg_width(src):
    with open(os.path.join(ROOT, src.lstrip("./")), encoding="utf-8") as f:
        return re.search(r'<svg[^>]*\swidth="(\d+)"', f.read(600)).group(1)


class ResponsiveTests(unittest.TestCase):
    def test_no_image_uses_a_small_percentage_width(self):
        for tag in IMG_TAGS:
            width = attribute(tag, "width")
            if width and width.endswith("%"):
                self.assertGreaterEqual(int(width[:-1]), 90, tag[:120])

    def test_only_small_images_have_a_fixed_height(self):
        for tag in IMG_TAGS:
            height = attribute(tag, "height")
            if height:
                self.assertLessEqual(int(height), 40, tag[:120])

    def test_card_images_use_a_fixed_pixel_width_that_matches_the_svg(self):
        for tag in IMG_TAGS:
            src = attribute(tag, "src") or ""
            if src.startswith(("assets/cards/", "assets/projects/")):
                width = attribute(tag, "width")
                self.assertIn(width, CARD_WIDTHS, src)
                self.assertEqual(width, svg_width(src), src)

    def test_heading_images_scale_by_width_not_height(self):
        for tag in IMG_TAGS:
            src = attribute(tag, "src") or ""
            if src.startswith("assets/headings/"):
                self.assertIsNotNone(attribute(tag, "width"), src)
                self.assertIsNone(attribute(tag, "height"), src)

    def test_chart_cards_use_widths_that_fit_side_by_side(self):
        for name, limit in (("streak-stats", 460), ("top-languages", 320), ("commit-stats", 320), ("productive-time", 320)):
            match = re.search(rf'<img width="(\d+)" src="./assets/{name}\.svg"', README)
            self.assertIsNotNone(match, name)
            self.assertLessEqual(int(match.group(1)), limit, name)

    def test_long_typing_animations_are_not_used(self):
        for url in re.findall(r"https://readme-typing-svg[^\"]+", README):
            width = int(re.search(r"[?&]width=(\d+)", url).group(1))
            self.assertLessEqual(width, 440, url)

    def test_readme_has_no_multi_column_tables(self):
        # Side-by-side table columns overflow on phones; only the one-cell header badge may remain.
        self.assertEqual(README.count("<table"), 1)
        self.assertEqual(README.count("<td"), 1)

    def test_hero_banner_has_a_pixel_width(self):
        self.assertIn('src="./assets/banner-3d.svg" width="340"', README)

    def test_hero_card_has_a_pixel_width(self):
        self.assertIn('src="assets/hero/hero-card.svg" width="440"', README)

    def test_hero_images_are_top_aligned(self):
        block = README.split("<!-- HERO:START -->")[1].split("<!-- HERO:END -->")[0]
        self.assertEqual(block.count('align="top"'), 2)

    def test_activity_graph_is_shown_at_its_own_width(self):
        self.assertIn('<img src="./assets/contribution-activity.svg" width="640"', README)

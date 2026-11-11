"""Tests for the side-by-side hero (profile card + banner)."""
import json
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import make_hero  # noqa: E402

with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
    README = f.read()
with open(make_hero.CONTENT, encoding="utf-8") as f:
    HERO = json.load(f)["hero"]


class HeroContentTests(unittest.TestCase):
    def test_no_hero_text_was_lost(self):
        self.assertEqual(HERO["name"], "Hi, I\u2019m Samaun Rezvi")
        self.assertEqual(HERO["taglines"][0], "Full-Stack Web Developer")
        self.assertEqual(len(HERO["taglines"]), 3)
        self.assertIn("Daffodil International University", HERO["education"])
        self.assertEqual([r["name"] for r in HERO["roles"]], ["Full-Stack Developer", "UI/UX Minded", "Open to Work"])
        self.assertIn("open to opportunities", HERO["status"])

    def test_role_badge_files_exist(self):
        for role in HERO["roles"]:
            self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "badges", role["file"])), role["file"])

    def test_alt_text_carries_all_of_the_hero_text(self):
        alt = make_hero.alt_text(HERO)
        for text in [HERO["name"], *HERO["taglines"], HERO["education"], HERO["status"]]:
            self.assertIn(text, alt)


class HeroFilesTests(unittest.TestCase):
    def test_avatar_is_a_sharp_jpeg(self):
        with open(make_hero.AVATAR, "rb") as f:
            data = f.read()
        self.assertEqual(data[:3], b"\xff\xd8\xff")
        self.assertGreater(len(data), 30_000)
        self.assertLess(len(data), 150_000)

    def test_card_is_well_formed(self):
        with open(os.path.join(ROOT, "assets", "hero", "hero-card.svg"), encoding="utf-8") as f:
            root = ET.fromstring(f.read())
        self.assertEqual(root.get("width"), "440")

    def test_original_profile_photo_is_kept(self):
        self.assertTrue(os.path.exists(make_hero.SOURCE))


class HeroLayoutTests(unittest.TestCase):
    def test_readme_has_one_hero_block_with_both_images(self):
        self.assertEqual(README.count("<!-- HERO:START -->"), 1)
        self.assertEqual(README.count("<!-- HERO:END -->"), 1)
        block = README.split("<!-- HERO:START -->")[1].split("<!-- HERO:END -->")[0]
        self.assertEqual(block.count("<img"), 2)
        self.assertIn('width="440"', block)
        self.assertIn('width="340"', block)

    def test_banner_crop_matches_the_card_height(self):
        with open(os.path.join(ROOT, "assets", "banner-3d.svg"), encoding="utf-8") as f:
            head = f.read(700)
        width, height = (int(v) for v in re.search(r'width="(\d+)" height="(\d+)" viewBox', head).groups())
        shown_height = make_hero.BANNER_WIDTH * height / width
        self.assertAlmostEqual(shown_height, make_hero.card_kit.HERO_HEIGHT, delta=4)

    def test_both_images_fit_side_by_side_on_a_wide_screen(self):
        self.assertLessEqual(make_hero.card_kit.HERO_WIDTH + make_hero.BANNER_WIDTH + 8, 820)

    def test_the_old_hero_pieces_are_not_duplicated_in_the_readme(self):
        self.assertNotIn("readme-typing-svg", README)
        self.assertNotIn("hero-name", README)


class AvatarQualityTests(unittest.TestCase):
    def jpeg_size(self):
        import struct
        with open(make_hero.AVATAR, "rb") as f:
            data = f.read()
        i = 2
        while i < len(data):
            marker = data[i + 1]
            if marker in (0xC0, 0xC2):
                height, width = struct.unpack(">HH", data[i + 5 : i + 9])
                return width, height
            i += 2 + struct.unpack(">H", data[i + 2 : i + 4])[0]
        self.fail("no frame header")

    def test_avatar_is_square(self):
        width, height = self.jpeg_size()
        self.assertEqual(width, height)

    def test_avatar_has_at_least_four_times_the_displayed_pixels(self):
        width, _ = self.jpeg_size()
        self.assertGreaterEqual(width, 96 * 4)

    def test_crop_stays_inside_the_source_photo(self):
        import struct
        with open(make_hero.SOURCE, "rb") as f:
            data = f.read()
        i = 2
        while i < len(data):
            marker = data[i + 1]
            if marker in (0xC0, 0xC2):
                src_h, src_w = struct.unpack(">HH", data[i + 5 : i + 9])
                break
            i += 2 + struct.unpack(">H", data[i + 2 : i + 4])[0]
        x, y, size = make_hero.CROP
        self.assertLessEqual(x + size, src_w)
        self.assertLessEqual(y + size, src_h)


class HeroCardMarkupTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "assets", "hero", "hero-card.svg"), encoding="utf-8") as f:
            self.svg = f.read()

    def test_card_has_a_title(self):
        self.assertIn("<title>", self.svg)

    def test_avatar_is_clipped_to_a_circle(self):
        self.assertIn('id="face"', self.svg)
        self.assertIn('clip-path="url(#face)"', self.svg)

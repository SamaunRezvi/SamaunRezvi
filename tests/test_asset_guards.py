"""Guards for the size and format of the generated and self-hosted assets."""
import glob
import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def files(pattern):
    return glob.glob(os.path.join(ROOT, *pattern.split("/")))


class BadgeSizeTests(unittest.TestCase):
    def test_each_badge_is_under_20_kb(self):
        badges = files("assets/badges/*.svg")
        self.assertTrue(badges)
        for path in badges:
            self.assertLess(os.path.getsize(path), 20_000, os.path.basename(path))


class CardSizeTests(unittest.TestCase):
    def test_each_card_is_under_120_kb(self):
        for pattern in ("assets/cards/*.svg", "assets/projects/*.svg"):
            for path in files(pattern):
                self.assertLess(os.path.getsize(path), 120_000, path)

    def test_the_hero_card_is_under_250_kb(self):
        self.assertLess(os.path.getsize(os.path.join(ROOT, "assets", "hero", "hero-card.svg")), 250_000)


class HeadingSizeTests(unittest.TestCase):
    def test_each_heading_is_under_10_kb(self):
        for path in files("assets/headings/*.svg"):
            self.assertLess(os.path.getsize(path), 10_000, path)


class FontFileTests(unittest.TestCase):
    def test_fonts_start_with_the_woff2_signature(self):
        fonts = files("assets/fonts/*.woff2")
        self.assertEqual(len(fonts), 2)
        for path in fonts:
            with open(path, "rb") as f:
                self.assertEqual(f.read(4), b"wOF2", path)

    def test_each_font_subset_is_under_100_kb(self):
        for path in files("assets/fonts/*.woff2"):
            self.assertLess(os.path.getsize(path), 100_000, path)


class MetricsFileTests(unittest.TestCase):
    def test_widths_are_positive_numbers(self):
        import json
        with open(os.path.join(ROOT, "assets", "fonts", "metrics.json"), encoding="utf-8") as f:
            table = json.load(f)
        for family, widths in table.items():
            self.assertTrue(widths, family)
            for char, width in widths.items():
                self.assertGreater(width, 0, f"{family} {char!r}")

    def test_basic_latin_is_covered(self):
        import json
        with open(os.path.join(ROOT, "assets", "fonts", "metrics.json"), encoding="utf-8") as f:
            table = json.load(f)
        for family, widths in table.items():
            for char in "abcxyzABCXYZ0129 .,":
                self.assertIn(char, widths, f"{family} {char!r}")


class SelfHostedTests(unittest.TestCase):
    def test_no_remote_image_or_font_references(self):
        for pattern in ("assets/cards/*.svg", "assets/headings/*.svg", "assets/hero/*.svg", "assets/projects/*.svg"):
            for path in files(pattern):
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                self.assertNotIn('href="http', text, path)
                self.assertNotIn("url(http", text, path)
                self.assertNotIn("@import", text, path)


class NoScriptTests(unittest.TestCase):
    def test_svgs_have_no_script_tags_or_event_handlers(self):
        for pattern in ("assets/cards/*.svg", "assets/headings/*.svg", "assets/hero/*.svg", "assets/projects/*.svg", "assets/badges/*.svg"):
            for path in files(pattern):
                with open(path, encoding="utf-8") as f:
                    text = f.read().lower()
                self.assertNotIn("<script", text, path)
                self.assertNotIn(" onload=", text, path)
                self.assertNotIn(" onclick=", text, path)

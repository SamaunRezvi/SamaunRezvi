"""Guards for the README: images resolve, badges are self-hosted and the design stays intact."""
import json
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BADGE_DIR = os.path.join(ROOT, "assets", "badges")

with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
    README = f.read()
with open(os.path.join(BADGE_DIR, "manifest.json"), encoding="utf-8") as f:
    MANIFEST = json.load(f)

TAGS = re.findall(r"<img\b[^>]*>", README)
SOURCES = [m.group(1) for m in (re.search(r'src="([^"]+)"', tag) for tag in TAGS) if m]
LOCAL = [s for s in SOURCES if not s.startswith("http")]
BADGES = [s for s in LOCAL if s.startswith("assets/badges/")]
GREENS = ["3FB950", "238636", "2EA043", "56D364", "7EE787", "A2F2B0", "6DB33F"]


class ReadmeAssetTests(unittest.TestCase):
    def test_local_images_exist(self):
        for source in LOCAL:
            self.assertTrue(os.path.exists(os.path.join(ROOT, source)), source)

    def test_badge_files_are_svgs(self):
        for source in BADGES:
            with open(os.path.join(ROOT, source), "rb") as f:
                self.assertTrue(f.read().lstrip().startswith(b"<svg"), source)

    def test_every_manifest_entry_has_a_file(self):
        for name in MANIFEST:
            self.assertTrue(os.path.exists(os.path.join(BADGE_DIR, name)), name)

    def test_no_badge_file_is_orphaned(self):
        files = {name for name in os.listdir(BADGE_DIR) if name.endswith(".svg")}
        self.assertEqual(files, set(MANIFEST))

    def test_every_readme_badge_is_in_the_manifest(self):
        for source in BADGES:
            self.assertIn(os.path.basename(source), MANIFEST)

    def test_only_live_shields_badges_are_remote(self):
        for source in SOURCES:
            if source.startswith("https://img.shields.io"):
                self.assertTrue("/github/followers/" in source or "/github/stars/" in source, source)

    def test_manifest_urls_point_to_shields(self):
        for url in MANIFEST.values():
            self.assertTrue(url.startswith("https://img.shields.io/"), url)

    def test_every_image_has_alt_text(self):
        for tag in TAGS:
            self.assertIn("alt=", tag)

    def test_no_green_accent_colours_remain(self):
        for colour in GREENS:
            self.assertNotIn(colour.lower(), README.lower(), colour)

    def test_recent_projects_markers_appear_once_in_order(self):
        start = README.count("<!-- RECENT_PROJECTS:START -->")
        end = README.count("<!-- RECENT_PROJECTS:END -->")
        self.assertEqual((start, end), (1, 1))
        self.assertLess(README.index("RECENT_PROJECTS:START"), README.index("RECENT_PROJECTS:END"))

    def test_typing_animations_are_kept_to_a_few(self):
        self.assertLessEqual(README.count("readme-typing-svg"), 4)

    def test_decorative_gradient_dividers_are_kept_to_a_few(self):
        self.assertLessEqual(README.count("capsule-render"), 3)

    def test_typing_animations_use_the_serif_font(self):
        urls = re.findall(r'https://readme-typing-svg[^"]+', README)
        for url in urls:
            self.assertIn("font=Playfair+Display", url)

    def test_typing_animations_are_large_enough_to_read(self):
        for url in re.findall(r'https://readme-typing-svg[^"]+', README):
            size = int(re.search(r"[?&]size=(\d+)", url).group(1))
            self.assertGreaterEqual(size, 19, url)

    def test_static_captions_are_not_shrunk_with_sub(self):
        for caption in ("what I reach for and why", "architecture walkthrough on request"):
            line = next(l for l in README.splitlines() if caption in l)
            self.assertNotIn("<sub>", line)

    def test_body_text_is_not_shrunk_with_sub(self):
        self.assertNotIn("<sub>", README)

    def test_badge_logos_do_not_embed_the_old_greens(self):
        import base64
        import glob

        for path in glob.glob(os.path.join(BADGE_DIR, "*.svg")):
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for payload in re.findall(r"base64,([A-Za-z0-9+/=]+)", text):
                decoded = base64.b64decode(payload).decode("utf-8", "ignore").lower()
                for colour in GREENS:
                    self.assertNotIn("#" + colour.lower(), decoded, os.path.basename(path))

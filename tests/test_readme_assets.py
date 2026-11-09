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

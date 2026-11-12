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

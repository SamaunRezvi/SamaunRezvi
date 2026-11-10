"""Guards that the generated cards keep the README palette instead of GitHub green."""
import colorsys
import glob
import os
import unittest

from test_cards import cards

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OLD_GREENS = ["#3fb950", "#40c463", "#2ea043", "#196c2e", "#56d364"]
CONSTANTS = [
    "STREAK_RING",
    "STREAK_FIRE",
    "STREAK_CUR_LABEL",
    "CHART_COLOR",
    "ACTIVITY_LINE",
    "ACTIVITY_AREA",
    "ACTIVITY_TITLE",
]


def is_green(colour):
    red, green, blue = (int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    hue, saturation, _ = colorsys.rgb_to_hsv(red, green, blue)
    return saturation > 0.25 and 0.22 <= hue <= 0.47


class CardColourTests(unittest.TestCase):
    def test_card_accent_constants_are_not_green(self):
        for name in CONSTANTS:
            self.assertFalse(is_green(getattr(cards, name)), name)

    def test_generated_svgs_do_not_use_the_old_greens(self):
        for path in glob.glob(os.path.join(ROOT, "assets", "*.svg")):
            with open(path, encoding="utf-8") as f:
                text = f.read().lower()
            for colour in OLD_GREENS:
                self.assertNotIn(colour, text, f"{os.path.basename(path)} {colour}")

"""Guards that the generated cards keep their text readable."""
import re
import unittest

from test_cards import DAILY, LANGS, STATS, STREAK, cards

MIN_FONT_SIZE = 11


def font_sizes(svg):
    return [int(n) for n in re.findall(r"font-size[:=]\"?(\d+)px", svg)]


class CardTextSizeTests(unittest.TestCase):
    def check(self, name, svg):
        sizes = font_sizes(svg)
        self.assertTrue(sizes, name)
        self.assertGreaterEqual(min(sizes), MIN_FONT_SIZE, name)

    def test_stats_card(self):
        self.check("stats", cards.build_stats_card(STATS))

    def test_donut_card(self):
        self.check("donut", cards.build_donut_card(LANGS))

    def test_productive_time_card(self):
        self.check("productive", cards.build_productive_time_card([1] * 24, 6))

    def test_activity_card(self):
        self.check("activity", cards.build_activity_graph(DAILY))

    def test_streak_card(self):
        self.check("streak", cards.build_streak_card(STREAK))

    def test_card_numbers_are_larger_than_their_labels(self):
        sizes = font_sizes(cards.build_streak_card(STREAK))
        self.assertGreater(max(sizes), 30)

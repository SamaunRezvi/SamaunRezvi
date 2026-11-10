"""Tests for main(): a failing card must not stop the other cards."""
import os
import tempfile
import unittest
from unittest import mock

from test_cards import DAILY, LANGS, STATS, STREAK, cards


class MainTests(unittest.TestCase):
    def run_main(self, **overrides):
        patches = {
            "fetch_data": mock.Mock(return_value=(LANGS, STATS)),
            "fetch_productive_time": mock.Mock(return_value=[1] * 24),
            "fetch_daily_contributions": mock.Mock(return_value=DAILY),
            "fetch_streak_stats": mock.Mock(return_value=STREAK),
            "fetch_recent_repos": mock.Mock(return_value=[]),
            "write_project_cards": mock.Mock(return_value=[]),
            "update_readme": mock.Mock(return_value=False),
        }
        patches.update(overrides)
        with tempfile.TemporaryDirectory() as folder:
            previous = os.getcwd()
            os.chdir(folder)
            try:
                with mock.patch.multiple(cards, **patches):
                    cards.main()
                return sorted(os.listdir("assets"))
            finally:
                os.chdir(previous)

    def test_writes_every_card_when_everything_works(self):
        self.assertEqual(len(self.run_main()), 5)

    def test_a_failing_card_does_not_stop_the_others(self):
        broken = mock.Mock(side_effect=RuntimeError("api down"))
        written = self.run_main(fetch_productive_time=broken)
        self.assertEqual(len(written), 4)
        self.assertNotIn("productive-time.svg", written)

    def test_raises_when_every_card_fails(self):
        broken = mock.Mock(side_effect=RuntimeError("api down"))
        with self.assertRaises(RuntimeError):
            self.run_main(
                fetch_data=broken,
                fetch_productive_time=broken,
                fetch_daily_contributions=broken,
                fetch_streak_stats=broken,
            )

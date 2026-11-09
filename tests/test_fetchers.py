"""Unit tests for the GitHub data fetchers, with the GraphQL layer mocked out."""
import datetime
import os
import sys
import types
import unittest
from unittest import mock

try:
    import requests  # noqa: F401
except ImportError:  # the fetchers under test are fed mocked data
    sys.modules["requests"] = types.ModuleType("requests")

os.environ.setdefault("GITHUB_TOKEN", "test-token")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".github", "scripts"))

import generate_profile_cards as cards  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


class FixedDateTime(datetime.datetime):
    """A datetime whose now() is frozen at NOW."""

    @classmethod
    def now(cls, tz=None):
        return NOW if tz is None else NOW.astimezone(tz)


def frozen_time():
    clock = types.SimpleNamespace(
        datetime=FixedDateTime,
        date=datetime.date,
        timedelta=datetime.timedelta,
        timezone=datetime.timezone,
    )
    return mock.patch.object(cards, "datetime", clock)


def calendar(days):
    day_list = [{"date": d, "contributionCount": c} for d, c in days]
    weeks = [{"contributionDays": day_list}]
    return {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": weeks}}}}


class GqlTests(unittest.TestCase):
    def post(self, payload):
        response = mock.Mock()
        response.json.return_value = payload
        client = mock.Mock()
        client.post.return_value = response
        return mock.patch.object(cards, "requests", client)

    def test_returns_the_data_payload(self):
        with self.post({"data": {"user": {"id": "1"}}}):
            self.assertEqual(cards.gql("query", {}), {"user": {"id": "1"}})

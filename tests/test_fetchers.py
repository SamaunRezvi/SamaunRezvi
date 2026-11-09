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

    def test_raises_on_graphql_errors(self):
        with self.post({"errors": [{"message": "boom"}]}):
            with self.assertRaises(RuntimeError):
                cards.gql("query", {})

    def test_sends_the_bearer_token(self):
        with self.post({"data": {}}) as client:
            cards.gql("query", {})
        headers = client.post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], f"Bearer {cards.TOKEN}")


class DailyContributionTests(unittest.TestCase):
    def run_fetch(self, rows, **kwargs):
        with frozen_time(), mock.patch.object(cards, "gql", return_value=calendar(rows)):
            return cards.fetch_daily_contributions(**kwargs)

    def test_returns_one_entry_per_day(self):
        self.assertEqual(len(self.run_fetch([])), 31)
        self.assertEqual(len(self.run_fetch([], days=10)), 10)

    def test_fills_missing_days_with_zero(self):
        result = self.run_fetch([("2026-11-07", 4)])
        self.assertIn((7, 4), result)
        self.assertEqual(sum(count for _, count in result), 4)


def history(*dates):
    edges = [{"node": {"authoredDate": d}} for d in dates]
    return {"repository": {"defaultBranchRef": {"target": {"history": {"edges": edges}}}}}


class ProductiveTimeTests(unittest.TestCase):
    def run_fetch(self, repos, offset=6.0):
        def fake(query, variables):
            if "commitContributionsByRepository" in query:
                data = {"commitContributionsByRepository": repos}
                return {"user": {"contributionsCollection": data}}
            return {"user": {"id": "user-id"}}

        with mock.patch.object(cards, "gql", side_effect=fake):
            with mock.patch.object(cards, "UTC_OFFSET", offset):
                return cards.fetch_productive_time()

    def test_returns_24_hourly_buckets(self):
        self.assertEqual(len(self.run_fetch([])), 24)

    def test_shifts_the_hour_by_the_utc_offset(self):
        result = self.run_fetch([history("2026-11-01T10:00:00Z")])
        self.assertEqual(result[16], 1)
        self.assertEqual(sum(result), 1)

    def test_wraps_past_midnight(self):
        result = self.run_fetch([history("2026-11-01T20:00:00Z")])
        self.assertEqual(result[2], 1)

    def test_skips_repos_without_a_default_branch(self):
        empty = {"repository": {"defaultBranchRef": None}}
        result = self.run_fetch([empty, history("2026-11-01T10:00:00Z")])
        self.assertEqual(sum(result), 1)


def repo(stars, **languages):
    edges = [{"size": size, "node": {"name": name}} for name, size in languages.items()]
    return {"stargazerCount": stars, "languages": {"edges": edges}}


class FetchDataTests(unittest.TestCase):
    def run_fetch(self, repos, years=(2025, 2026)):
        summary = {
            "totalPullRequestContributions": 3,
            "totalIssueContributions": 2,
            "totalRepositoriesWithContributedCommits": 5,
            "contributionYears": list(years),
        }

        def fake(query, variables):
            if "repositories(" in query:
                nodes = {"nodes": repos}
                return {"user": {"repositories": nodes, "contributionsCollection": summary}}
            return {"user": {"contributionsCollection": {"totalCommitContributions": 10}}}

        http = mock.Mock()
        http.get.side_effect = Exception("offline")
        with mock.patch.object(cards, "gql", side_effect=fake):
            with mock.patch.object(cards, "requests", http):
                return cards.fetch_data()

    def test_sums_stars_across_repos(self):
        _, stats = self.run_fetch([repo(2, Python=1), repo(3, Python=1)])
        self.assertEqual({label: value for _, label, value in stats}["Total Stars:"], "5")

    def test_sums_commits_across_years(self):
        _, stats = self.run_fetch([repo(0, Python=1)])
        self.assertEqual({label: value for _, label, value in stats}["Total Commits:"], "20")

    def test_aggregates_languages_and_sorts_by_size(self):
        langs, _ = self.run_fetch([repo(0, Python=100, HTML=10), repo(0, Python=50, CSS=500)])
        self.assertEqual([lang["name"] for lang in langs], ["CSS", "Python", "HTML"])
        self.assertEqual(langs[1]["value"], 150)

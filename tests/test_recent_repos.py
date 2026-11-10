"""Tests for the Latest Public Projects section."""
import os
import tempfile
import unittest
from unittest import mock

from test_cards import cards


def repo(name="demo", **overrides):
    data = {
        "name": name,
        "url": f"https://github.com/me/{name}",
        "description": "A demo project",
        "stargazerCount": 3,
        "pushedAt": "2026-11-09T10:00:00Z",
        "primaryLanguage": {"name": "TypeScript"},
    }
    data.update(overrides)
    return data


class RenderTests(unittest.TestCase):
    def test_shows_name_link_and_facts(self):
        html = cards.render_recent_repos([repo()])
        self.assertIn('<a href="https://github.com/me/demo"><code>demo/</code></a>', html)
        self.assertIn("TypeScript", html)
        self.assertIn("\u2605 3", html)
        self.assertIn("updated Nov 9, 2026", html)

    def test_escapes_html_in_descriptions(self):
        html = cards.render_recent_repos([repo(description="<script>alert(1)</script>")])
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_handles_missing_description_and_language(self):
        html = cards.render_recent_repos([repo(description=None, primaryLanguage=None)])
        self.assertIn("No description yet.", html)

    def test_shortens_long_descriptions(self):
        html = cards.render_recent_repos([repo(description="word " * 100)])
        shown = html.split("<sub>")[1].split("</sub>")[0]
        self.assertLessEqual(len(shown), cards.MAX_DESCRIPTION)
        self.assertTrue(shown.endswith("…"))

    def test_pads_each_row_to_three_cells(self):
        self.assertEqual(cards.render_recent_repos([repo()]).count("<td"), 3)
        self.assertEqual(cards.render_recent_repos([repo(str(i)) for i in range(4)]).count("<td"), 6)

    def test_shows_a_placeholder_when_there_are_no_repos(self):
        self.assertIn("No public repositories", cards.render_recent_repos([]))


class FetchTests(unittest.TestCase):
    def test_skips_the_profile_repository_itself(self):
        nodes = [repo(cards.USERNAME), repo("one"), repo("two")]
        reply = {"user": {"repositories": {"nodes": nodes}}}
        with mock.patch.object(cards, "gql", return_value=reply):
            names = [r["name"] for r in cards.fetch_recent_repos(limit=2)]
        self.assertEqual(names, ["one", "two"])


class UpdateReadmeTests(unittest.TestCase):
    def write(self, folder, text):
        path = os.path.join(folder, "README.md")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        return path

    def read(self, path):
        with open(path, encoding="utf-8", newline="") as f:
            return f.read()

    def test_replaces_only_the_marked_block(self):
        text = f"before\n{cards.RECENT_START}\nold\n{cards.RECENT_END}\nafter\n"
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, text)
            self.assertTrue(cards.update_readme("new", path))
            self.assertEqual(
                self.read(path),
                f"before\n{cards.RECENT_START}\nnew\n{cards.RECENT_END}\nafter\n",
            )

    def test_returns_false_when_nothing_changes(self):
        text = f"{cards.RECENT_START}\nsame\n{cards.RECENT_END}\n"
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, text)
            self.assertFalse(cards.update_readme("same", path))

    def test_returns_false_without_markers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, "no markers here\n")
            self.assertFalse(cards.update_readme("x", path))
            self.assertEqual(self.read(path), "no markers here\n")

    def test_keeps_windows_line_endings(self):
        text = f"a\r\n{cards.RECENT_START}\r\nold\r\n{cards.RECENT_END}\r\n"
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, text)
            cards.update_readme("one\ntwo", path)
            self.assertNotIn("\n", self.read(path).replace("\r\n", ""))

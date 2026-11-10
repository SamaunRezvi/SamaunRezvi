"""Tests for the Latest Public Projects section."""
import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

from test_cards import cards


def repo(name="demo", **overrides):
    data = {
        "name": name,
        "url": f"https://github.com/me/{name}",
        "description": "PH_B-14_A08 - Demo App: A demo project",
        "stargazerCount": 0,
        "pushedAt": "2026-11-09T10:00:00Z",
        "homepageUrl": None,
        "primaryLanguage": {"name": "TypeScript"},
        "repositoryTopics": {"nodes": [{"topic": {"name": "nextjs"}}]},
    }
    data.update(overrides)
    return data


class ProjectCardSpecTests(unittest.TestCase):
    def spec(self, index=0, **overrides):
        return cards.project_card_spec(repo(**overrides), index)

    def test_uses_the_professional_title_and_keeps_the_repo_name(self):
        spec = self.spec()
        self.assertEqual(spec["title"], "Demo App")
        self.assertEqual(spec["code"], "demo")
        self.assertNotIn("PH_B-14", spec["body"])

    def test_eyebrow_is_the_language(self):
        self.assertEqual(self.spec()["eyebrow"], "TypeScript")
        self.assertEqual(self.spec(primaryLanguage=None)["eyebrow"], "Repository")

    def test_chips_combine_the_language_and_topics(self):
        self.assertEqual(self.spec()["chips"], ["TypeScript", "nextjs"])

    def test_chips_are_unique_and_capped_at_four(self):
        nodes = [{"topic": {"name": n}} for n in ("TypeScript", "a", "b", "c", "d")]
        self.assertEqual(len(self.spec(repositoryTopics={"nodes": nodes})["chips"]), 4)

    def test_footer_offers_a_live_demo_only_with_a_homepage(self):
        self.assertEqual(self.spec()["footer_right"], "Source code \u2192")
        self.assertEqual(self.spec(homepageUrl="https://demo.example.com")["footer_right"], "Live demo \u2192")

    def test_ignores_homepages_that_are_not_web_links(self):
        self.assertEqual(self.spec(homepageUrl="javascript:alert(1)")["footer_right"], "Source code \u2192")

    def test_shows_the_updated_date(self):
        self.assertEqual(self.spec()["footer_left"], "Updated Nov 9, 2026")

    def test_cards_cycle_through_distinct_accents(self):
        self.assertNotEqual(self.spec(0)["accent"], self.spec(1)["accent"])
        self.assertEqual(self.spec(0)["number"], "01")
        self.assertEqual(self.spec(5)["number"], "06")

    def test_handles_missing_description_and_topics(self):
        spec = self.spec(description=None, repositoryTopics=None)
        self.assertEqual(spec["body"], "No description yet.")


class ShortenTests(unittest.TestCase):
    def test_capitalises_the_first_letter(self):
        self.assertEqual(cards.shorten("a dark, sleek library"), "A dark, sleek library")

    def test_cuts_long_text_at_a_word_boundary(self):
        shown = cards.shorten("alpha " * 80)
        self.assertLessEqual(len(shown), cards.MAX_DESCRIPTION)
        self.assertTrue(shown.endswith("\u2026"))
        self.assertTrue(all(word.lower() == "alpha" for word in shown[:-1].split()))

    def test_keeps_short_text_unchanged(self):
        self.assertEqual(cards.shorten("Short text."), "Short text.")


class RenderTests(unittest.TestCase):
    def test_images_link_to_the_repository(self):
        html = cards.render_recent_repos([repo()])
        self.assertIn('<a href="https://github.com/me/demo"><img', html)
        self.assertIn('src="assets/projects/demo.svg"', html)

    def test_two_cards_per_row(self):
        html = cards.render_recent_repos([repo(str(i)) for i in range(3)])
        self.assertEqual(html.count('<p align="center">'), 2)

    def test_lists_live_demos_only_when_present(self):
        plain = cards.render_recent_repos([repo()])
        live = cards.render_recent_repos([repo(homepageUrl="https://demo.example.com")])
        self.assertNotIn("Live demos", plain)
        self.assertIn('Live demos: <a href="https://demo.example.com">Demo App</a>', live)

    def test_alt_text_is_escaped(self):
        html = cards.render_recent_repos([repo(description='<b>"x"</b>')])
        self.assertNotIn("<b>", html)
        self.assertIn("&quot;", html)

    def test_placeholder_when_there_are_no_repos(self):
        self.assertIn("No public repositories", cards.render_recent_repos([]))

    def test_project_text_is_not_shrunk_with_sub(self):
        self.assertNotIn("<sub>", cards.render_recent_repos([repo()]))


class WriteProjectCardsTests(unittest.TestCase):
    def test_writes_one_well_formed_svg_per_repo(self):
        with tempfile.TemporaryDirectory() as folder:
            names = cards.write_project_cards([repo("one"), repo("two")], folder)
            self.assertEqual(names, ["one.svg", "two.svg"])
            for name in names:
                ET.parse(os.path.join(folder, name))

    def test_removes_cards_of_repos_that_are_gone(self):
        with tempfile.TemporaryDirectory() as folder:
            cards.write_project_cards([repo("one"), repo("two")], folder)
            cards.write_project_cards([repo("one")], folder)
            self.assertEqual(os.listdir(folder), ["one.svg"])

    def test_slug_is_file_safe(self):
        self.assertEqual(cards.project_slug({"name": "My Repo/Name"}), "my-repo-name")


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

"""Tests for turning repository names and descriptions into professional project titles."""
import unittest

from test_cards import cards


def split(name, description):
    return cards.split_project_text({"name": name, "description": description})


class ProjectTitleTests(unittest.TestCase):
    def test_uses_the_name_before_the_colon(self):
        title, summary = split(
            "assignment_eight_s",
            "PH_B-14_A08 - StudioSpace API: A secure Express and MongoDB backend.",
        )
        self.assertEqual(title, "StudioSpace API")
        self.assertEqual(summary, "A secure Express and MongoDB backend.")

    def test_uses_a_quoted_product_name(self):
        title, summary = split(
            "assignment_five",
            'PH_B-14_A05 - A sleek, responsive "Dev Stack Builder" website.',
        )
        self.assertEqual(title, "Dev Stack Builder")
        self.assertEqual(summary, 'A sleek, responsive "Dev Stack Builder" website.')

    def test_uses_curly_quoted_names(self):
        title, _ = split("assignment_one", "PH_B-14_A01 - A landing page for \u201cDevConf 2026\u201d.")
        self.assertEqual(title, "DevConf 2026")

    def test_falls_back_to_a_readable_repo_name(self):
        title, summary = split("my-portfolio_site", "A personal portfolio")
        self.assertEqual(title, "My Portfolio Site")
        self.assertEqual(summary, "A personal portfolio")

    def test_handles_a_missing_description(self):
        title, summary = split("assignment_one", None)
        self.assertEqual(title, "Assignment One")
        self.assertEqual(summary, "No description yet.")

    def test_ignores_a_long_text_before_a_colon(self):
        long_lead = "This is a very long sentence that is not a project name"
        title, summary = split("demo", f"{long_lead}: and more")
        self.assertEqual(title, "Demo")
        self.assertEqual(summary, f"{long_lead}: and more")

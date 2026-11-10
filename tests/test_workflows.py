"""Guards for the GitHub Actions workflows."""
import glob
import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def workflow(name):
    with open(os.path.join(ROOT, ".github", "workflows", name), encoding="utf-8") as f:
        return f.read()


class WorkflowTests(unittest.TestCase):
    def test_snake_uses_the_custom_palette_not_github_green(self):
        text = workflow("snake.yml")
        self.assertNotIn("palette=github", text)
        self.assertEqual(text.count("color_dots="), 2)

    def test_profile_details_green_is_recoloured(self):
        text = workflow("profile-card.yml")
        self.assertIn('svg.replace("#40c463", "#BC8CFF")', text)

    def test_every_workflow_has_a_timeout(self):
        for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            with open(path, encoding="utf-8") as f:
                self.assertIn("timeout-minutes", f.read(), os.path.basename(path))

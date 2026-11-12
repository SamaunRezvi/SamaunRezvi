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

    def test_profile_details_uses_the_serif_font(self):
        self.assertIn("Times New Roman", workflow("profile-card.yml"))

    def test_profile_details_text_is_enlarged(self):
        self.assertIn("int(m.group(1)) + 2", workflow("profile-card.yml"))

    def test_card_workflow_commits_the_project_cards(self):
        self.assertIn("git add README.md assets/projects", workflow("profile-card.yml"))

    def test_card_workflow_commits_the_readme_section(self):
        self.assertIn("git add README.md assets/", workflow("profile-card.yml"))

    def test_every_workflow_has_a_timeout(self):
        for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            with open(path, encoding="utf-8") as f:
                self.assertIn("timeout-minutes", f.read(), os.path.basename(path))


class ActionVersionTests(unittest.TestCase):
    def test_every_action_is_pinned_to_a_version(self):
        import re
        for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    match = re.search(r"uses:\s*(\S+)", line)
                    if match:
                        self.assertRegex(match.group(1), r"@[\w.]+$", f"{os.path.basename(path)}: {line.strip()}")


class WorkflowShapeTests(unittest.TestCase):
    def test_every_workflow_has_a_name_and_a_trigger(self):
        for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertTrue(text.startswith("name:"), os.path.basename(path))
            self.assertIn("\non:", text, os.path.basename(path))


class ConcurrencyTests(unittest.TestCase):
    def test_groups_are_unique(self):
        import re
        groups = []
        for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            match = re.search(r"group:\s*(\S+)", open(path, encoding="utf-8").read())
            if match:
                groups.append(match.group(1))
        self.assertEqual(len(groups), len(set(groups)))


class CronTests(unittest.TestCase):
    def test_cron_has_five_fields(self):
        import re
        found = 0
        for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            for expr in re.findall(r'cron:\s*"([^"]+)"', open(path, encoding="utf-8").read()):
                found += 1
                self.assertEqual(len(expr.split()), 5, expr)
        self.assertGreater(found, 0)


class PermissionTests(unittest.TestCase):
    def test_write_access_is_only_for_committing_workflows(self):
        for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
            text = open(path, encoding="utf-8").read()
            if "contents: write" in text:
                self.assertIn("git push", text + "git push" if "push" in text else text, os.path.basename(path))
            if "git push" in text:
                self.assertIn("contents: write", text, os.path.basename(path))


class ManualRunTests(unittest.TestCase):
    def test_generators_have_workflow_dispatch(self):
        for name in ("3d-contrib.yml", "profile-card.yml", "snake.yml"):
            self.assertIn("workflow_dispatch", workflow(name), name)

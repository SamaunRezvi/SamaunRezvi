"""Tests for tools/check.py."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import check  # noqa: E402


class CheckScriptTests(unittest.TestCase):
    def test_steps_are_named_and_runnable(self):
        self.assertTrue(check.STEPS)
        for name, command in check.STEPS:
            self.assertTrue(name)
            self.assertTrue(command[0])

    def test_script_paths_exist(self):
        for _, command in check.STEPS:
            for part in command:
                if part.endswith(".py"):
                    self.assertTrue(os.path.exists(os.path.join(ROOT, part)), part)


class HeroMarkerTests(unittest.TestCase):
    def test_source_checks_for_both_markers(self):
        with open(os.path.join(ROOT, "tools", "make_hero.py"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("HERO:START", source)
        self.assertIn("is missing the HERO", source)


class CropTests(unittest.TestCase):
    def test_crop_is_a_positive_square(self):
        import make_hero
        x, y, size = make_hero.CROP
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertGreater(size, 0)


class IssueTemplateTests(unittest.TestCase):
    def test_bug_template_has_front_matter(self):
        path = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "bug_report.md")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("---\nname:"))
        self.assertEqual(text.count("---"), 2)

    def test_security_contact_link_points_at_the_policy(self):
        path = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "config.yml")
        with open(path, encoding="utf-8") as f:
            self.assertIn("SECURITY.md", f.read())


class FastFlagTests(unittest.TestCase):
    def test_fast_uses_only_the_first_step(self):
        from unittest import mock
        with mock.patch.object(check.subprocess, "run") as fake:
            fake.return_value.returncode = 0
            self.assertEqual(check.main(["--fast"]), 0)
            self.assertEqual(fake.call_count, 1)

    def test_default_runs_every_step(self):
        from unittest import mock
        with mock.patch.object(check.subprocess, "run") as fake:
            fake.return_value.returncode = 0
            self.assertEqual(check.main([]), 0)
            self.assertEqual(fake.call_count, len(check.STEPS))

    def test_failure_returns_one(self):
        from unittest import mock
        with mock.patch.object(check.subprocess, "run") as fake:
            fake.return_value.returncode = 1
            self.assertEqual(check.main(["--fast"]), 1)

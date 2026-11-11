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

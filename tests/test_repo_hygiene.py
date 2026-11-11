"""Repository hygiene guards: writing style, placeholders and file basics."""
import glob
import json
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP = {".git", "assets", "profile-3d-contrib", "__pycache__", "node_modules"}
TEXT = (".py", ".md", ".yml", ".json")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def text_files():
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        found += [os.path.join(folder, f) for f in files if f.endswith(TEXT)]
    return found


def doc_files():
    return [p for p in text_files() if p.endswith(".md")] + [os.path.join(ROOT, "README.md")]


class PlaceholderTests(unittest.TestCase):
    def test_no_placeholder_text_in_docs(self):
        banned = ["lorem ipsum", "todo: fill in", "example.com", "your-username-here"]
        for path in doc_files():
            text = read(path).lower()
            for phrase in banned:
                self.assertNotIn(phrase, text, f"{phrase} in {path}")


class AttributionTests(unittest.TestCase):
    def test_no_tool_names(self):
        words = ["clau" + "de", "anthro" + "pic", "code" + "x", "copi" + "lot", "chat" + "gpt"]
        for path in text_files() + [os.path.join(ROOT, "README.md")]:
            text = read(path).lower()
            for word in words:
                self.assertNotIn(word, text, path)


class PythonStyleTests(unittest.TestCase):
    def python_files(self):
        return [p for p in text_files() if p.endswith(".py")]

    def test_no_tabs(self):
        for path in self.python_files():
            self.assertNotIn("\t", read(path), path)

    def test_no_trailing_whitespace(self):
        for path in self.python_files():
            for number, line in enumerate(read(path).splitlines(), 1):
                self.assertEqual(line, line.rstrip(), f"{path}:{number}")

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


class FileEndingTests(unittest.TestCase):
    def test_files_end_with_one_newline(self):
        for path in text_files():
            text = read(path)
            self.assertTrue(text.endswith("\n"), path)
            self.assertFalse(text.endswith("\n\n"), path)


class ScriptEntryTests(unittest.TestCase):
    def test_scripts_have_a_main_guard(self):
        scripts = glob.glob(os.path.join(ROOT, "tools", "*.py")) + glob.glob(os.path.join(ROOT, ".github", "scripts", "generate_*.py"))
        self.assertTrue(scripts)
        for path in scripts:
            self.assertIn('if __name__ == "__main__":', read(path), path)


class CardContentTests(unittest.TestCase):
    def strings(self, value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from self.strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from self.strings(item)

    def test_no_empty_or_padded_strings(self):
        data = json.loads(read(".github/cards-content.json"))
        for text in self.strings(data):
            self.assertTrue(text, "empty string")
            self.assertEqual(text, text.strip(), repr(text))

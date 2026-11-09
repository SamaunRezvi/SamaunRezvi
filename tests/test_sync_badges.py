"""Unit tests for tools/sync_badges.py."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import sync_badges  # noqa: E402

SVG = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'


class HelperTests(unittest.TestCase):
    def test_is_svg_accepts_svg_bytes(self):
        self.assertTrue(sync_badges.is_svg(b"  \n" + SVG))

    def test_is_svg_rejects_html(self):
        self.assertFalse(sync_badges.is_svg(b"<html>Too Many Requests</html>"))

    def test_encode_url_leaves_ascii_urls_unchanged(self):
        url = "https://img.shields.io/badge/Next.js-0d1117?style=flat-square&logo=nextdotjs"
        self.assertEqual(sync_badges.encode_url(url), url)

    def test_encode_url_encodes_non_ascii_characters(self):
        encoded = sync_badges.encode_url("https://img.shields.io/badge/●_LIVE-F0883E")
        self.assertTrue(encoded.isascii())
        self.assertIn("%E2%97%8F", encoded)


class ManifestAndSyncTests(unittest.TestCase):
    def test_load_manifest_reads_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "manifest.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"a.svg": "https://example.com/a"}, f)
            self.assertEqual(sync_badges.load_manifest(path), {"a.svg": "https://example.com/a"})

    def test_check_reports_missing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            problems = sync_badges.check({"a.svg": "u"}, folder)
        self.assertEqual(problems, ["missing: a.svg"])

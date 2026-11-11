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

    def test_check_reports_files_that_are_not_svgs(self):
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "a.svg"), "wb") as f:
                f.write(b"<html></html>")
            problems = sync_badges.check({"a.svg": "u"}, folder)
        self.assertEqual(problems, ["not an SVG: a.svg"])

    def test_sync_only_downloads_missing_files_unless_refreshing(self):
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "have.svg"), "wb") as f:
                f.write(SVG)
            manifest = {"have.svg": "u1", "need.svg": "u2"}
            fetched = []

            def fetch(url):
                fetched.append(url)
                return SVG

            self.assertEqual(sync_badges.sync(manifest, folder, fetch=fetch), ["need.svg"])
            self.assertEqual(fetched, ["u2"])
            refreshed = sync_badges.sync(manifest, folder, refresh=True, fetch=fetch)
            self.assertEqual(sorted(refreshed), ["have.svg", "need.svg"])


class ManifestShapeTests(unittest.TestCase):
    def test_manifest_is_a_string_to_string_mapping(self):
        manifest = sync_badges.load_manifest()
        self.assertTrue(manifest)
        for name, url in manifest.items():
            self.assertTrue(name.endswith(".svg"), name)
            self.assertTrue(url.startswith("https://"), url)

    def test_file_names_have_no_path_parts(self):
        for name in sync_badges.load_manifest():
            self.assertEqual(os.path.basename(name), name)

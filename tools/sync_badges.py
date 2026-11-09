"""Keep the self-hosted README badges in assets/badges/ in sync with shields.io.

Usage:
    python tools/sync_badges.py            # download badges that are missing
    python tools/sync_badges.py --refresh  # re-download every badge
    python tools/sync_badges.py --check    # verify every listed badge exists and is an SVG
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BADGE_DIR = os.path.join(ROOT, "assets", "badges")
MANIFEST = os.path.join(BADGE_DIR, "manifest.json")


def load_manifest(path=MANIFEST):
    """Return the {file name: source URL} mapping."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def encode_url(url):
    """Percent-encode non-ASCII characters so urllib can request the URL."""
    return urllib.parse.quote(url, safe=":/?&=%#@,+;$!*'()~._-")


def is_svg(data):
    """Return True when the bytes look like an SVG document."""
    return data.lstrip().startswith(b"<svg")

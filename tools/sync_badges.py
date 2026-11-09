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


def download(url, retries=5, delay=2.0):
    """Download a badge, retrying on failure, and return the SVG bytes."""
    last = None
    for _ in range(retries):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            request = urllib.request.Request(encode_url(url), headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
            if is_svg(data):
                return data
            last = ValueError("response is not an SVG")
        except Exception as error:  # network errors are retried
            last = error
        time.sleep(delay)
    raise RuntimeError(f"could not download {url}: {last}")


def sync(manifest, directory=BADGE_DIR, refresh=False, fetch=download):
    """Download missing badges (all of them with refresh) and return the written names."""
    written = []
    for name, url in manifest.items():
        path = os.path.join(directory, name)
        if os.path.exists(path) and not refresh:
            continue
        with open(path, "wb") as f:
            f.write(fetch(url))
        written.append(name)
    return written


def check(manifest, directory=BADGE_DIR):
    """Return a list of problems: badge files that are missing or not SVGs."""
    problems = []
    for name in manifest:
        path = os.path.join(directory, name)
        if not os.path.exists(path):
            problems.append(f"missing: {name}")
            continue
        with open(path, "rb") as f:
            if not is_svg(f.read()):
                problems.append(f"not an SVG: {name}")
    return problems

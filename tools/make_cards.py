"""Generate the Principles and Selected Work card images and place them in the README.

The text lives in .github/cards-content.json. Run this after editing it:

    python tools/make_cards.py

It writes assets/cards/*.svg and rewrites the blocks between the
<!-- CARDS:principles:START --> and <!-- CARDS:work:START --> markers in README.md.
"""
import base64
import json
import os
import re
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

import card_kit  # noqa: E402

CONTENT = os.path.join(ROOT, ".github", "cards-content.json")
OUT = os.path.join(ROOT, "assets", "cards")
README = os.path.join(ROOT, "README.md")
ACRONYMS = {"iot": "IoT", "api": "API", "ui": "UI", "ux": "UX"}


def humanize(folder):
    """Turn a folder name such as 'iot-monitoring/' into 'IoT Monitoring'."""
    words = re.split(r"[-_/]+", folder.strip("/"))
    return " ".join(ACRONYMS.get(word.lower(), word.capitalize()) for word in words if word)


def badge_image(filename):
    """Return (data URI, width, height) for a self-hosted badge file."""
    with open(os.path.join(ROOT, "assets", "badges", filename), "rb") as f:
        data = f.read()
    size = re.search(rb'width="(\d+)" height="(\d+)"', data)
    uri = "data:image/svg+xml;base64," + base64.b64encode(data).decode("ascii")
    return uri, int(size.group(1)), int(size.group(2))


def principle_specs(items):
    """Card specs for the Principles I Build On section."""
    return [
        {
            "accent": card_kit.ACCENTS[i % len(card_kit.ACCENTS)],
            "eyebrow": f"Principle {i + 1:02d}",
            "number": f"{i + 1:02d}",
            "title": item["title"],
            "code": item["code"],
            "body": item["body"],
        }
        for i, item in enumerate(items)
    ]


def work_specs(items):
    """Card specs for the Selected Work section."""
    return [
        {
            "accent": card_kit.ACCENTS[i % len(card_kit.ACCENTS)],
            "eyebrow": f"Project {i + 1:02d}",
            "number": f"{i + 1:02d}",
            "title": humanize(item["folder"]),
            "code": item["folder"],
            "body": item["body"],
            "badges": [badge_image(name) for name in item["badges"]],
        }
        for i, item in enumerate(items)
    ]


def grid_html(prefix, specs, items):
    """Two cards per row as centred images."""
    images = []
    for i, spec in enumerate(specs):
        alt = escape(f"{spec['title']}: {spec['body']}", {'"': "&quot;"})
        images.append(f'<img alt="{alt}" src="assets/cards/{prefix}-{i + 1}.svg" width="49%" />')
    rows = ["<p align=\"center\">\n" + "\n".join(images[i : i + 2]) + "\n</p>" for i in range(0, len(images), 2)]
    return "\n".join(rows)


def replace_block(text, name, html):
    """Replace the text between the CARDS markers of one block."""
    start, end = f"<!-- CARDS:{name}:START -->", f"<!-- CARDS:{name}:END -->"
    a, b = text.index(start) + len(start), text.index(end)
    return text[:a] + "\n" + html + "\n" + text[b:]


def main():
    """Write the card SVGs and refresh the README blocks."""
    with open(CONTENT, encoding="utf-8") as f:
        content = json.load(f)
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.endswith(".svg"):
            os.remove(os.path.join(OUT, old))
    groups = [
        ("principle", "principles", principle_specs(content["principles"]), content["principles"]),
        ("work", "work", work_specs(content["work"]), content["work"]),
    ]
    with open(README, encoding="utf-8", newline="") as f:
        readme = f.read()
    newline = "\r\n" if "\r\n" in readme else "\n"
    readme = readme.replace("\r\n", "\n")
    for prefix, name, specs, items in groups:
        for i, svg in enumerate(card_kit.equalise(specs)):
            with open(os.path.join(OUT, f"{prefix}-{i + 1}.svg"), "w", encoding="utf-8", newline="\n") as f:
                f.write(svg)
        readme = replace_block(readme, name, grid_html(prefix, specs, items))
        print(f"wrote {len(specs)} {prefix} cards")
    with open(README, "w", encoding="utf-8", newline="") as f:
        f.write(readme.replace("\n", newline))


if __name__ == "__main__":
    main()

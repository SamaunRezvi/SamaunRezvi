"""Generate the README card images from .github/cards-content.json and place them in the README.

Edit the text in the JSON file, then run:

    python tools/make_cards.py

It writes assets/cards/*.svg and rewrites the blocks between the
<!-- CARDS:name:START --> and <!-- CARDS:name:END --> markers in README.md.

Cards are fixed-width images (420px, 270px or 168px) so they sit side by side on
wide screens and stack on phones, where GitHub shrinks an image to the screen width.
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


def accent(index):
    """Accent colour for the card at a position, cycling through the palette."""
    return card_kit.ACCENTS[index % len(card_kit.ACCENTS)]


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
            "accent": accent(i),
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
            "accent": accent(i),
            "eyebrow": f"Project {i + 1:02d}",
            "number": f"{i + 1:02d}",
            "title": humanize(item["folder"]),
            "code": item["folder"],
            "body": item["body"],
            "badges": [badge_image(name) for name in item["badges"]],
        }
        for i, item in enumerate(items)
    ]


def stat_specs(items):
    """Specs for the four About Me statistic cards."""
    return [
        {
            "accent": accent(i),
            "label": item["label"],
            "number": item["number"],
            "title": item["title"],
            "caption": item["caption"],
        }
        for i, item in enumerate(items)
    ]


def tech_specs(items):
    """Card specs for the Tech & Tools categories."""
    return [
        {
            "accent": accent(i),
            "eyebrow": f"Stack {i + 1:02d}",
            "number": f"{i + 1:02d}",
            "title": item["title"],
            "badges": [badge_image(badge["file"]) for badge in item["badges"]],
        }
        for i, item in enumerate(items)
    ]


def quote_specs(items):
    """Card specs for the Words To Code By quotes."""
    return [
        {
            "accent": accent(i),
            "eyebrow": f"Quote {i + 1:02d}",
            "number": "“",
            "title": item["quote"],
            "title_size": 21,
            "footer_left": item["author"],
        }
        for i, item in enumerate(items)
    ]


def contact_specs(items):
    """Card specs for the Get In Touch cards."""
    return [
        {
            "accent": accent(i),
            "width": 270,
            "eyebrow": "Open to",
            "title": item["title"],
            "title_size": 22,
            "body": item["body"],
        }
        for i, item in enumerate(items)
    ]


def alt_text(prefix, item, spec):
    """Alt text carrying all the card's information for screen readers."""
    if prefix == "stat":
        return f"{spec['number']} {spec['title']}: {spec['caption']}"
    if prefix == "tech":
        return f"{spec['title']}: " + ", ".join(badge["name"] for badge in item["badges"])
    if prefix == "quote":
        return f"{spec['title']} — {spec['footer_left']}"
    return f"{spec['title']}: {spec['body']}"


# prefix, content key, spec builder, image width in px, cards per row
GROUPS = [
    ("principle", "principles", principle_specs, 420, 2),
    ("work", "work", work_specs, 420, 2),
    ("stat", "stats", stat_specs, card_kit.STAT_WIDTH, 4),
    ("tech", "tech", tech_specs, 420, 2),
    ("quote", "quotes", quote_specs, 420, 2),
    ("contact", "contact", contact_specs, 270, 3),
]


def render_group(prefix, specs, per_row):
    """Render the SVG markup for every card of a group."""
    if prefix == "stat":
        return [card_kit.render_stat(spec) for spec in specs]
    return card_kit.equalise(specs, per_row)


def grid_html(prefix, specs, items, width, per_row):
    """Cards as centred images, several per row."""
    images = []
    for i, spec in enumerate(specs):
        alt = escape(alt_text(prefix, items[i], spec), {'"': "&quot;"})
        images.append(f'<img alt="{alt}" src="assets/cards/{prefix}-{i + 1}.svg" width="{width}" />')
    rows = ['<p align="center">\n' + "\n".join(images[i : i + per_row]) + "\n</p>" for i in range(0, len(images), per_row)]
    return "\n".join(rows)


def replace_block(text, name, html):
    """Replace the text between the CARDS markers of one block."""
    start, end = f"<!-- CARDS:{name}:START -->", f"<!-- CARDS:{name}:END -->"
    if start not in text or end not in text:
        raise ValueError(f"README.md is missing the {name} card markers")
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
    with open(README, encoding="utf-8", newline="") as f:
        readme = f.read()
    newline = "\r\n" if "\r\n" in readme else "\n"
    readme = readme.replace("\r\n", "\n")
    for prefix, key, builder, width, per_row in GROUPS:
        items = content[key]
        specs = builder(items)
        for i, svg in enumerate(render_group(prefix, specs, per_row)):
            with open(os.path.join(OUT, f"{prefix}-{i + 1}.svg"), "w", encoding="utf-8", newline="\n") as f:
                f.write(svg)
        readme = replace_block(readme, key, grid_html(prefix, specs, items, width, per_row))
        print(f"wrote {len(specs)} {prefix} cards")
    with open(README, "w", encoding="utf-8", newline="") as f:
        f.write(readme.replace("\n", newline))


if __name__ == "__main__":
    main()

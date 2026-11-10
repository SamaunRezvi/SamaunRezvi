"""Generate the serif README headings in assets/headings/ with the font embedded.

GitHub strips CSS from README markdown, so the only way to show a custom font is
as an image. Each heading is an SVG with a tiny subset of the font embedded as
base64, in a dark and a light variant (the README picks one with <picture>).

Usage:
    python tools/make_headings.py

Network access (Google Fonts) is only needed when you run this; the generated
SVGs are committed, so viewers never depend on it.
"""
import base64
import os
import re
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "headings")

FAMILY = "Playfair Display"
WEIGHT = 600
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
THEMES = {"dark": "#E6EDF3", "light": "#1F2328"}
ACCENT = ("#58A6FF", "#BC8CFF", "#F778BA")
FALLBACK = f"'{FAMILY}', 'Times New Roman', Times, serif"

# slug, text, font size, width, anchor, accent bar
HEADINGS = [
    ("hero-name", "Hi, I’m Samaun Rezvi", 40, 430, "start", True),
    ("about-me", "About Me", 42, 760, "middle", True),
    ("principles", "Principles I Build On", 30, 760, "middle", True),
    ("tech-and-tools", "Tech & Tools", 42, 760, "middle", True),
    ("selected-work", "Selected Work", 42, 760, "middle", True),
    ("latest-projects", "Latest Public Projects", 42, 760, "middle", True),
    ("github-activity", "GitHub Activity", 42, 760, "middle", True),
    ("contribution-landscape", "Contribution Landscape", 42, 760, "middle", True),
    ("commit-habits", "Commit Habits", 42, 760, "middle", True),
    ("contribution-snake", "Contribution Snake", 42, 760, "middle", True),
    ("words-to-code-by", "Words To Code By", 42, 760, "middle", True),
    ("get-in-touch", "Get In Touch", 42, 760, "middle", True),
    ("stat-projects", "15+", 58, 170, "middle", False),
    ("stat-stack", "10+", 58, 170, "middle", False),
    ("stat-reach", "2", 58, 170, "middle", False),
    ("stat-ownership", "99.9%", 58, 170, "middle", False),
]


def heading_height(size):
    """Height of a heading SVG for a given font size."""
    return round(size * 1.35) + 16


def font_faces(text):
    """Return @font-face CSS embedding only the glyphs needed for the text."""
    url = (
        "https://fonts.googleapis.com/css2?family="
        f"{FAMILY.replace(' ', '+')}:wght@{WEIGHT}&text={urllib.parse.quote(text)}"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    css = urllib.request.urlopen(request, timeout=30).read().decode("utf-8")
    faces = []
    for block in re.findall(r"@font-face\s*\{[^}]*\}", css):
        source = re.search(r"url\((https://[^)]+)\)", block).group(1)
        data = urllib.request.urlopen(
            urllib.request.Request(source, headers={"User-Agent": USER_AGENT}), timeout=30
        ).read()
        encoded = base64.b64encode(data).decode("ascii")
        ranges = re.search(r"unicode-range:\s*([^;]+);", block)
        unicode_range = f"unicode-range:{ranges.group(1)};" if ranges else ""
        faces.append(
            f"@font-face{{font-family:'{FAMILY}';font-weight:{WEIGHT};"
            f"src:url(data:font/woff2;base64,{encoded}) format('woff2');{unicode_range}}}"
        )
    return "".join(faces)


def build_svg(text, size, width, anchor, bar, color, faces):
    """Return the SVG markup for one heading in one colour."""
    height = heading_height(size)
    x = width / 2 if anchor == "middle" else 0
    bar_x = (width - 56) / 2 if anchor == "middle" else 0
    accent = ""
    if bar:
        accent = (
            '<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="0">'
            f'<stop offset="0" stop-color="{ACCENT[0]}"/>'
            f'<stop offset="0.5" stop-color="{ACCENT[1]}"/>'
            f'<stop offset="1" stop-color="{ACCENT[2]}"/></linearGradient></defs>'
            f'<rect x="{bar_x:g}" y="{height - 4}" width="56" height="2" rx="1" fill="url(#g)"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(text)}">'
        f"<title>{escape(text)}</title>"
        f"<style>{faces}text{{font-family:{FALLBACK};font-weight:{WEIGHT};"
        f"font-variant-numeric:lining-nums;letter-spacing:0.4px}}</style>"
        f"{accent}"
        f'<text x="{x:g}" y="{round(size * 1.05)}" font-size="{size}" '
        f'text-anchor="{anchor}" fill="{color}">{escape(text)}</text>'
        "</svg>\n"
    )


def main():
    """Download the font subsets and write every heading SVG."""
    os.makedirs(OUT, exist_ok=True)
    for slug, text, size, width, anchor, bar in HEADINGS:
        faces = font_faces(text)
        for theme, color in THEMES.items():
            svg = build_svg(text, size, width, anchor, bar, color, faces)
            with open(os.path.join(OUT, f"{slug}-{theme}.svg"), "w", encoding="utf-8", newline="\n") as f:
                f.write(svg)
        print(f"wrote {slug}")


if __name__ == "__main__":
    main()

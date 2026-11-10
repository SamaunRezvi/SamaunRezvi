"""Draw the README project and principle cards as self-contained SVG images.

GitHub strips CSS from README markdown, so rich cards have to be images. These
SVGs embed a small serif font subset and wrap their text with measured glyph
widths (assets/fonts/metrics.json), so they look the same everywhere and need
no browser to generate.
"""
import base64
import json
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

TITLE_FONT = ("Playfair Display", 600, "playfair-600.woff2")
BODY_FONT = ("Source Serif 4", 400, "sourceserif-400.woff2")
MONO = "ui-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
SERIF_FALLBACK = "'Times New Roman', Times, serif"

WIDTH = 420
PAD = 26
ACCENTS = ["#58A6FF", "#BC8CFF", "#F778BA", "#F0883E", "#E3B341", "#39D0D8"]

_cache = {}


def metrics():
    """Return {font family: {character: advance width per 1000 units}}."""
    if "metrics" not in _cache:
        with open(os.path.join(FONT_DIR, "metrics.json"), encoding="utf-8") as f:
            _cache["metrics"] = json.load(f)
    return _cache["metrics"]


def font_css():
    """Return @font-face rules with both fonts embedded as base64."""
    if "css" not in _cache:
        rules = []
        for family, weight, filename in (TITLE_FONT, BODY_FONT):
            with open(os.path.join(FONT_DIR, filename), "rb") as f:
                data = base64.b64encode(f.read()).decode("ascii")
            rules.append(
                f"@font-face{{font-family:'{family}';font-weight:{weight};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2');}}"
            )
        _cache["css"] = "".join(rules)
    return _cache["css"]


def text_width(text, family, size, spacing=0.0):
    """Width in pixels of text set in a card font; unknown characters count as 0.55em."""
    table = metrics()[family]
    units = sum(table.get(ch, 550) for ch in text)
    return units * size / 1000 + spacing * len(text)


def wrap(text, family, size, max_width):
    """Greedy word wrap using measured glyph widths; returns a list of lines."""
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and text_width(candidate, family, size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def lighten(colour, amount=0.35):
    """Mix a #RRGGBB colour with white."""
    channels = [int(colour[i : i + 2], 16) for i in (1, 3, 5)]
    mixed = [round(c + (255 - c) * amount) for c in channels]
    return "#" + "".join(f"{c:02X}" for c in mixed)


def layout(spec, min_height=0):
    """Compute positions for a card spec and return (items, height)."""
    inner = WIDTH - 2 * PAD
    items = []
    y = PAD + 11
    items.append(("eyebrow", y, spec.get("eyebrow", "")))
    y += 36
    title_lines = wrap(spec["title"], TITLE_FONT[0], 24, inner - 20)
    for line in title_lines:
        items.append(("title", y, line))
        y += 30
    y -= 30
    if spec.get("code"):
        top = y + 16
        items.append(("code", top, spec["code"]))
        y = top + 24
    body_lines = wrap(spec.get("body", ""), BODY_FONT[0], 14.5, inner)
    if body_lines:
        y += 20
        for line in body_lines:
            items.append(("body", y + 14, line))
            y += 22
    chips = spec.get("chips") or []
    badges = spec.get("badges") or []
    if chips or badges:
        y += 18
        x, row_top = 0, y
        for label in chips:
            width = text_width(label, BODY_FONT[0], 12.5) + 22
            if x and x + width > inner:
                x, row_top = 0, row_top + 34
            items.append(("chip", row_top, label, x, width))
            x += width + 8
        for data_uri, bw, bh in badges:
            width = bw * 24 / bh
            if x and x + width > inner:
                x, row_top = 0, row_top + 34
            items.append(("badge", row_top, data_uri, x, width))
            x += width + 8
        y = row_top + 26
    if spec.get("footer_left") or spec.get("footer_right"):
        height = max(y + 16 + 22 + 18, min_height)
        items.append(("footer", height - 18, spec.get("footer_left", ""), spec.get("footer_right", "")))
    else:
        height = max(y + PAD, min_height)
    return items, round(height)


def natural_height(spec):
    """Height a card needs for its content."""
    return layout(spec)[1]


def render(spec, min_height=0):
    """Return the SVG markup for one card spec."""
    items, height = layout(spec, min_height)
    accent = spec.get("accent", ACCENTS[0])
    soft = lighten(accent)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(spec["title"])}">',
        f"<title>{escape(spec['title'])}</title>",
        f"<style>{font_css()}"
        f".t{{font-family:'{TITLE_FONT[0]}',{SERIF_FALLBACK};font-weight:600;font-variant-numeric:lining-nums}}"
        f".b{{font-family:'{BODY_FONT[0]}',{SERIF_FALLBACK};font-weight:400}}"
        f".m{{font-family:{MONO}}}</style>",
        "<defs>"
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#151d2b"/><stop offset="1" stop-color="#0d1117"/></linearGradient>'
        f'<radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
        f'gradientTransform="translate(40 20) scale(260)">'
        f'<stop offset="0" stop-color="{accent}" stop-opacity="0.22"/>'
        f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="{soft}" stop-opacity="0.15"/></linearGradient>'
        f'<clipPath id="clip"><rect width="{WIDTH}" height="{height}" rx="16"/></clipPath>'
        "</defs>",
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="16" fill="url(#bg)" stroke="#2b3445"/>',
        '<g clip-path="url(#clip)">',
        f'<rect width="{WIDTH}" height="{height}" fill="url(#glow)"/>',
        f'<rect width="{WIDTH}" height="4" fill="url(#bar)"/>',
        "</g>",
    ]
    if spec.get("number"):
        parts.append(
            f'<text class="t" x="{WIDTH - PAD}" y="{PAD + 54}" text-anchor="end" font-size="68" '
            f'fill="{accent}" fill-opacity="0.14">{escape(spec["number"])}</text>'
        )
    for item in items:
        kind, y = item[0], item[1]
        if kind == "eyebrow":
            parts.append(
                f'<text class="b" x="{PAD}" y="{y}" font-size="11" letter-spacing="1.8" '
                f'fill="{accent}">{escape(item[2].upper())}</text>'
            )
        elif kind == "title":
            parts.append(f'<text class="t" x="{PAD}" y="{y}" font-size="24" fill="#E6EDF3">{escape(item[2])}</text>')
        elif kind == "code":
            width = len(item[2]) * 7.3 + 22
            parts.append(
                f'<rect x="{PAD}" y="{y}" width="{width:.1f}" height="24" rx="8" fill="#1a2231" stroke="#2b3649"/>'
                f'<text class="m" x="{PAD + 11}" y="{y + 16}" font-size="12" fill="#9DB0CC">{escape(item[2])}</text>'
            )
        elif kind == "body":
            parts.append(f'<text class="b" x="{PAD}" y="{y}" font-size="14.5" fill="#C3CDD9">{escape(item[2])}</text>')
        elif kind == "chip":
            _, row_top, label, x, width = item
            parts.append(
                f'<rect x="{PAD + x:.1f}" y="{row_top}" width="{width:.1f}" height="26" rx="13" '
                f'fill="{accent}" fill-opacity="0.12" stroke="{accent}" stroke-opacity="0.5"/>'
                f'<text class="b" x="{PAD + x + width / 2:.1f}" y="{row_top + 17.5}" text-anchor="middle" '
                f'font-size="12.5" fill="{soft}">{escape(label)}</text>'
            )
        elif kind == "badge":
            _, row_top, data_uri, x, width = item
            parts.append(
                f'<image x="{PAD + x:.1f}" y="{row_top}" width="{width:.1f}" height="24" href="{data_uri}"/>'
            )
        elif kind == "footer":
            _, base, left, right = item
            parts.append(f'<line x1="{PAD}" y1="{base - 22}" x2="{WIDTH - PAD}" y2="{base - 22}" stroke="#222b3a"/>')
            if left:
                parts.append(f'<text class="b" x="{PAD}" y="{base}" font-size="12.5" fill="#8794AA">{escape(left)}</text>')
            if right:
                parts.append(
                    f'<text class="b" x="{WIDTH - PAD}" y="{base}" text-anchor="end" font-size="13" '
                    f'fill="{soft}">{escape(right)}</text>'
                )
    parts.append("</svg>\n")
    return "".join(parts)


def equalise(specs, per_row=2):
    """Render specs so that the cards in each row share the height of the tallest one."""
    svgs = []
    for start in range(0, len(specs), per_row):
        row = specs[start : start + per_row]
        tallest = max(natural_height(spec) for spec in row)
        svgs += [render(spec, min_height=tallest) for spec in row]
    return svgs

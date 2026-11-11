"""Generate the profile hero card and place it, next to the banner, in the README.

The text lives under "hero" in .github/cards-content.json. Run:

    python tools/make_hero.py            # rebuild the card and the README block
    python tools/make_hero.py --avatar   # also re-create the avatar from assets/image/SR (2).jpg

The hero is two fixed-width images in one centred paragraph (card 440px + banner 340px).
They sit side by side on a wide screen and stack on a narrow one, because GitHub
shrinks images that are wider than the screen and wraps them.
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

import card_kit  # noqa: E402

CONTENT = os.path.join(ROOT, ".github", "cards-content.json")
OUT = os.path.join(ROOT, "assets", "hero")
AVATAR = os.path.join(OUT, "avatar.jpg")
SOURCE = os.path.join(ROOT, "assets", "image", "SR (2).jpg")
# Square crop (x, y, size) around the face in the 1200x1128 source photo; no retouching.
CROP = (95, 50, 1030)
README = os.path.join(ROOT, "README.md")
BANNER_WIDTH = 340
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def resize_avatar(size=480):
    """Crop the source photo to a square around the face and shrink it to a sharp JPEG (5x the displayed size)."""
    browser = next((path for path in BROWSERS if os.path.exists(path)), None)
    if not browser:
        raise SystemExit("Install Edge or Chrome to resize the avatar.")
    with open(SOURCE, "rb") as f:
        source = base64.b64encode(f.read()).decode("ascii")
    page = (
        "<html><body><pre id='out'>pending</pre><script>"
        "const img=new Image();img.onload=()=>{"
        f"const c=document.createElement('canvas');c.width=c.height={size};"
        "const g=c.getContext('2d');g.imageSmoothingEnabled=true;g.imageSmoothingQuality='high';"
        f"g.drawImage(img,{CROP[0]},{CROP[1]},{CROP[2]},{CROP[2]},0,0,{size},{size});"
        "document.getElementById('out').textContent=c.toDataURL('image/jpeg',0.95);};"
        f"img.src='data:image/jpeg;base64,{source}';</script></body></html>"
    )
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "resize.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(page)
        result = subprocess.run(
            [browser, "--headless", "--disable-gpu", "--virtual-time-budget=20000", "--dump-dom", "file:///" + path.replace("\\", "/")],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    match = re.search(r"data:image/jpeg;base64,([A-Za-z0-9+/=]+)", result.stdout)
    if not match:
        raise SystemExit("Could not resize the avatar.")
    os.makedirs(OUT, exist_ok=True)
    with open(AVATAR, "wb") as f:
        f.write(base64.b64decode(match.group(1)))


def data_uri(path, mime):
    """Return a base64 data URI for a file."""
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def badge(filename):
    """Return (data URI, width, height) for a self-hosted badge."""
    path = os.path.join(ROOT, "assets", "badges", filename)
    with open(path, "rb") as f:
        size = re.search(rb'width="(\d+)" height="(\d+)"', f.read(400))
    return data_uri(path, "image/svg+xml"), int(size.group(1)), int(size.group(2))


def hero_spec(hero):
    """Build the card_kit spec from the hero content."""
    return {
        "avatar": data_uri(AVATAR, "image/jpeg"),
        "name": hero["name"],
        "taglines": hero["taglines"],
        "education": hero["education"],
        "roles": [badge(role["file"]) for role in hero["roles"]],
        "status": hero["status"],
    }


def alt_text(hero):
    """All the hero card's text, for screen readers."""
    roles = ", ".join(role["name"] for role in hero["roles"])
    return f"{hero['name']} {' / '.join(hero['taglines'])}. {hero['education']}. {roles}. {hero['status']}"


def block_html(hero):
    """The README block: hero card and banner side by side."""
    alt = escape(alt_text(hero), {'"': "&quot;"})
    return (
        '<p align="center">\n'
        f'<img align="top" alt="{alt}" src="assets/hero/hero-card.svg" width="{card_kit.HERO_WIDTH}" />\n'
        f'<img align="top" alt="Animated banner" src="./assets/banner-3d.svg" width="{BANNER_WIDTH}" />\n'
        "</p>"
    )


def main():
    """Write the hero card and refresh the README block."""
    if "--avatar" in sys.argv or not os.path.exists(AVATAR):
        resize_avatar()
    with open(CONTENT, encoding="utf-8") as f:
        hero = json.load(f)["hero"]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "hero-card.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(card_kit.render_hero(hero_spec(hero)))
    with open(README, encoding="utf-8", newline="") as f:
        text = f.read()
    newline = "\r\n" if "\r\n" in text else "\n"
    text = text.replace("\r\n", "\n")
    start, end = "<!-- HERO:START -->", "<!-- HERO:END -->"
    if start not in text or end not in text:
        raise SystemExit("README.md is missing the HERO:START or HERO:END marker.")
    a, b = text.index(start) + len(start), text.index(end)
    text = text[:a] + "\n" + block_html(hero) + "\n" + text[b:]
    with open(README, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", newline))
    print("wrote the hero card")


if __name__ == "__main__":
    main()

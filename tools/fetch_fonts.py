"""Download the card fonts and measure their glyph widths (run once, results are committed).

Writes into assets/fonts/:
  playfair-600.woff2    card titles
  sourceserif-400.woff2 card body text and chips
  metrics.json          advance width of every character per 1000 units, used to wrap text

The widths are measured in headless Edge or Chrome, because the card generator
must wrap text without a browser (it runs in GitHub Actions).

Usage:
    python tools/fetch_fonts.py
"""
import base64
import json
import os
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "fonts")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
CHARS = "".join(chr(c) for c in range(32, 127)) + "\u201c\u201d\u2018\u2019\u2026\u00b7\u2013\u2014\u2192\u2605\u00e9"
FONTS = [
    ("playfair-600", "Playfair Display", 600),
    ("sourceserif-400", "Source Serif 4", 400),
]
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def download(family, weight):
    """Return the woff2 bytes for a family and weight, limited to CHARS."""
    css_url = (
        "https://fonts.googleapis.com/css2?family="
        f"{family.replace(' ', '+')}:wght@{weight}&text={urllib.parse.quote(CHARS)}"
    )
    request = urllib.request.Request(css_url, headers={"User-Agent": USER_AGENT})
    css = urllib.request.urlopen(request, timeout=30).read().decode("utf-8")
    sources = re.findall(r"url\((https://[^)]+)\)", css)
    if len(sources) != 1:
        raise RuntimeError(f"expected one font file for {family}, got {len(sources)}")
    request = urllib.request.Request(sources[0], headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=30).read()


def measure(fonts):
    """Measure each character at 1000px in a headless browser and return {family: {char: width}}."""
    browser = next((path for path in BROWSERS if os.path.exists(path)), None)
    if not browser:
        raise SystemExit("Install Edge or Chrome to measure the fonts.")
    entries = [
        {"name": name, "weight": weight, "data": base64.b64encode(data).decode("ascii")}
        for name, weight, data in fonts
    ]
    page = (
        "<html><body><pre id='out'>pending</pre><script>"
        f"const fonts={json.dumps(entries)};const chars={json.dumps(CHARS)};"
        "(async()=>{const out={};"
        "for(const f of fonts){"
        "const face=new FontFace(f.name,`url(data:font/woff2;base64,${f.data})`,{weight:String(f.weight)});"
        "await face.load();document.fonts.add(face);"
        "const ctx=document.createElement('canvas').getContext('2d');"
        "ctx.font=`${f.weight} 1000px \"${f.name}\"`;out[f.name]={};"
        "for(const ch of chars){out[f.name][ch]=Math.round(ctx.measureText(ch).width*10)/10;}}"
        "document.getElementById('out').textContent=JSON.stringify(out);})();"
        "</script></body></html>"
    )
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "measure.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(page)
        result = subprocess.run(
            [browser, "--headless", "--disable-gpu", "--virtual-time-budget=20000", "--dump-dom", "file:///" + path.replace("\\", "/")],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    match = re.search(r"<pre id=\"out\">(\{.*?\})</pre>", result.stdout, re.S)
    if not match:
        raise SystemExit("Could not read the measurements from the browser.")
    return json.loads(match.group(1).replace("&quot;", '"'))


def main():
    """Download the fonts, measure them and write the metrics file."""
    os.makedirs(OUT, exist_ok=True)
    fonts = []
    for slug, family, weight in FONTS:
        data = download(family, weight)
        with open(os.path.join(OUT, f"{slug}.woff2"), "wb") as f:
            f.write(data)
        fonts.append((family, weight, data))
        print(f"wrote {slug}.woff2 ({len(data)} bytes)")
    metrics = measure(fonts)
    with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")
    print("wrote metrics.json")


if __name__ == "__main__":
    main()

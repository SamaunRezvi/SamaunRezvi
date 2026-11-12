# Fonts

Cards and headings are SVG images, so the fonts are embedded as base64 inside each file. GitHub does not load web fonts in a README, and an image cannot depend on the reader having them.

| Role | Font | File |
| --- | --- | --- |
| Titles and headings | Playfair Display, 600 | `assets/fonts/playfair-600.woff2` |
| Body text | Source Serif 4, 400 | `assets/fonts/sourceserif-400.woff2` |

Both fonts are open source (SIL Open Font License). The files are small subsets of the original fonts, cut to the characters the cards use.

`assets/fonts/metrics.json` holds each character's advance width. `card_kit.text_width` uses it to wrap text so a card is tall enough for what it says. Rebuild everything with `python tools/fetch_fonts.py`.

Plain text that is not an image, such as the Connect with Me badges' alt text, falls back to `Times New Roman`.

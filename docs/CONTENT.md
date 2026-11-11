# Editing the text

All text that appears on the generated cards lives in one file:
`.github/cards-content.json`.

| Key | What it feeds | Rebuild command |
| --- | --- | --- |
| `principles`, `work`, `stats`, `tech`, `quotes`, `contact` | the card grids in the README | `python tools/make_cards.py` |
| `hero` | the profile card next to the banner | `python tools/make_hero.py` |

Rules of thumb:

- Change the text in the JSON file, never in the generated SVGs.
- Keep titles unique inside a group (a test checks this).
- Cards are fixed-width images, so long text makes a card taller, not wider.
- The hero avatar is cut from `assets/image/SR (2).jpg`. Run `python tools/make_hero.py --avatar` after changing the crop in `tools/make_hero.py`.

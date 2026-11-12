# Testing

Run everything:

```bash
python tools/check.py
```

`python tools/check.py --fast` runs only the unit tests. Or run them directly:

```bash
python -m unittest discover -s tests -v
```

What the tests cover:

| File | Guards |
| --- | --- |
| `test_cards.py`, `test_fetchers.py`, `test_main.py` | data cards and GitHub queries |
| `test_card_kit.py`, `test_card_kit_helpers.py` | the shared SVG card renderer |
| `test_hero.py` | the hero card, avatar and banner |
| `test_responsive.py` | image widths so the README fits every screen |
| `test_readme_assets.py`, `test_static_cards.py`, `test_headings.py` | README images and generated cards |
| `test_repo_hygiene.py` | writing style and file basics |
| `test_workflows.py` | the GitHub Actions workflows |

Tests never call the GitHub API.

`check.py` also scans tracked text files (except the README, whose design is fixed) for long dashes and emoji.

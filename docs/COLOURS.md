# Colours

The README and every generated card use one palette on a dark background.

| Use | Hex |
| --- | --- |
| Blue (links, streak ring, hero tagline) | `#58A6FF` |
| Purple (charts, profile details) | `#BC8CFF` |
| Pink (gradient end, quotes) | `#F778BA` |
| Orange (streak flame, current day) | `#F0883E` |
| Gold | `#E3B341` |
| Cyan (activity graph) | `#39D0D8` |
| Card background | `#151D2B` to `#0D1117` |
| Card border | `#2B3445` |

The card accents are the first six rows and live in `ACCENTS` in `.github/scripts/card_kit.py`.

There is no green anywhere on purpose. `tests/test_card_colours.py` and `tests/test_readme_assets.py` fail if one comes back.

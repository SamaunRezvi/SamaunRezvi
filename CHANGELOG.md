# Changelog

Notable changes to this profile repository.

## 2026-11-06

- Replaced the green accents in the README with a blue, purple, pink and orange palette.
- Switched the 3D contribution graph to a custom season palette and tinted the base tiles.
- Added alt text to all README images for accessibility.
- Added `.gitattributes`, `.editorconfig` and extra `.gitignore` rules.

## 2026-11-07

- Added docstrings to the card generation script.
- Added job timeouts and concurrency groups to the workflows, plus Dependabot for Actions.

## 2026-11-08

- Added type hints to the card generation script.
- Added unit tests for the SVG card builders and a workflow that runs them.

## 2026-11-09

- Self-hosted the static README badges in `assets/badges/` after shields.io rate limits broke some images.
- Added `tools/sync_badges.py`.
- Added tests for the data fetchers, the badge sync tool and the README assets.

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

## 2026-11-10

- Fixed the contribution activity graph ending on tomorrow and dropping the oldest day.
- Fixed the productive time card undercounting commits (history was capped at 50 per repo).
- Total PRs and issues now cover every year, not only the last 12 months.
- One failing card query no longer stops the other cards from updating.
- Replaced the remaining green in the cards and the snake with the README palette.
- Added the Latest Public Projects section, generated from public repositories.

## 2026-11-10 (typography)

- Cut the typing animations from 14 to 4; useful lines became static captions.
- Removed the repeated gradient dividers.
- Section headings are now serif images (Playfair Display embedded) with dark and light variants.
- Remaining typing animations and the generated cards use a serif font.

## 2026-11-10 (cards)

- Principles, Selected Work and Latest Public Projects are now rich SVG cards with embedded serif fonts, accent gradients and tech tags.
- Project cards are generated from live repository data and show a Live demo label when a website is set.

## 2026-11-10 (responsive)

- About Me stats, Tech & Tools, quotes and contact are now cards; no content was removed (every stat, badge, quote and contact line is kept).
- Headings, chart cards and project cards scale correctly on phones and tablets.
- The hero is a single centred column.
- The contribution activity graph is narrower with larger labels.
- The LinkedIn badge logos no longer use GitHub green.

## 2026-11-10 (hero)

- The hero is side by side again: a profile card (avatar, name, rotating tagline, education, role badges, status) next to the banner. It stacks on narrow screens.
- The old typing-animation service is no longer used; the tagline is a self-hosted SVG animation.

## 2026-11-11

- The hero avatar now comes from a new high-resolution photo, cropped square and clipped to a circle, with the collar and tie visible.
- Added tests for asset sizes, fonts, workflow settings, README structure and renderer behaviour.
- Added guides for colours, fonts, responsive rules and workflows under `docs/`.

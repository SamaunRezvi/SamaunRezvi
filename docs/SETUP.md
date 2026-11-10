# Setup

How this profile repository is wired up and how to run it yourself.

## Prerequisites

- A GitHub repository named after your username (the profile repository).
- GitHub Actions enabled for the repository.
- Python 3.12 only if you want to run the card script locally.

## Token

The workflows read contribution data through the GraphQL API using a personal access token stored as the repository secret `PROFILE_PAT`. Create the token, then add it under *Settings > Secrets and variables > Actions*. Never commit the token.

## Workflows

| Workflow | Schedule (UTC) | Output |
| --- | --- | --- |
| `3d-contrib.yml` | 03:00 and 18:00 daily | `profile-3d-contrib/` |
| `profile-card.yml` | 03:30 and 18:30 daily | `assets/` |
| `snake.yml` | every 12 hours | `output` branch |

All three can also be started manually (`workflow_dispatch`) and run on every push to `main`.

## 3D graph colours

Colours for the 3D contribution graph live in `.github/3d-contrib-settings.json`. The `season` type takes four palettes (`contribColors1` to `contribColors4`); the first colour of each palette is the tile base for that part of the year. Edit the file, push, and the workflow regenerates `profile-3d-contrib/profile-custom.svg`.

## Running the card script locally

```bash
pip install requests
GITHUB_TOKEN=<token> USERNAME=<your-username> UTC_OFFSET=6 python .github/scripts/generate_profile_cards.py
```

The script writes the generated SVG cards into `assets/`. `UTC_OFFSET` shifts the commit-hour chart to your local time.

## Troubleshooting

- **Push rejected in a workflow:** the bot commits to `main` too. The workflows already fetch and rebase before retrying.
- **Cards look stale:** images are cached by GitHub; wait a few minutes or hard refresh.
- **A card is empty:** check that `PROFILE_PAT` exists and has not expired.

## Undo

Every card audit change is a separate commit and the old version is tagged. See [UNDO.md](UNDO.md).

## Latest Public Projects

The section between the `RECENT_PROJECTS` markers in `README.md` is rewritten by `profile-card.yml` from your public, non-fork repositories. Edit text outside the markers freely; text inside them is overwritten.

## Tests

The SVG builders have unit tests in `tests/`. Run them with:

```bash
pip install requests
python -m unittest discover -s tests -v
```

The `Tests` workflow runs the same command on every push and pull request.

## Badges

Static tech and section badges are self-hosted in `assets/badges/` so they keep working when shields.io is rate limited. `assets/badges/manifest.json` maps each file to its shields.io source URL.

```bash
python tools/sync_badges.py            # download badges that are missing
python tools/sync_badges.py --refresh  # re-download every badge
python tools/sync_badges.py --check    # verify the files exist and are SVGs
```

Only the followers and stars badges stay remote, because they show live numbers.

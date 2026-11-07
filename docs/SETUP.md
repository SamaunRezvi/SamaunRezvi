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

# Setup

How this profile repository is wired up and how to run it yourself.

## Prerequisites

- A GitHub repository named after your username (the profile repository).
- GitHub Actions enabled for the repository.
- Python 3.12 only if you want to run the card script locally.

## Token

The workflows read contribution data through the GraphQL API using a personal access token stored as the repository secret `PROFILE_PAT`. Create the token, then add it under *Settings > Secrets and variables > Actions*. Never commit the token.

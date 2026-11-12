# Workflows

| Workflow | Runs | What it commits |
| --- | --- | --- |
| `profile-card.yml` | twice a day and on every push | profile cards, the Latest Public Projects section |
| `3d-contrib.yml` | twice a day and on every push | the 3D contribution graph in `profile-3d-contrib/` |
| `snake.yml` | every 12 hours and on every push | the snake animation |
| `tests.yml` | every push and pull request | nothing, it only checks |

All of them can also be started by hand from the Actions tab. Each has a timeout and a concurrency group, so two runs of the same workflow never overlap.

The bot commits come from `github-actions[bot]`. If you only want to look at your own work, filter the history with `git log --author="Samaun"`.

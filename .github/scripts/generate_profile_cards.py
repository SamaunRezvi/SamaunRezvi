"""
Self-hosted, byte-for-byte reproduction of the old
github-profile-summary-cards "Top Languages by Repo" (donut chart),
"Stats" and "Productive Time" cards. The public
github-profile-summary-cards.vercel.app API that used to render these is
permanently dead (crashes with FUNCTION_INVOCATION_FAILED on every
endpoint), so this script recreates the exact same layout/colours from
that project's open-source templates and writes static SVGs into
assets/, refreshed daily by a workflow.
"""
import datetime
import math
import os
import re
import sys
from xml.sax.saxutils import escape

import requests

USERNAME = os.environ.get("USERNAME", "SamaunRezvi")
TOKEN = os.environ["GITHUB_TOKEN"]
UTC_OFFSET = float(os.environ.get("UTC_OFFSET", "6"))

# github_dark theme, taken from github-profile-summary-cards src/const/theme.ts
TITLE_COLOR = "#0366d6"
TEXT_COLOR = "#77909c"
BG_COLOR = "#0d1117"
STROKE_COLOR = "#2e343b"
ICON_COLOR = "#8b949e"
FONT = "'Times New Roman', Times, 'Liberation Serif', serif"

# Octicon-style SVG paths used by the Stats card (16x16 viewBox).
ICONS = {
    "GITHUB": '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>',
    "STAR": '<path fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 01-.564-.41L8 2.694v.001z"></path>',
    "COMMIT": '<path fill-rule="evenodd" d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.001 4.001 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z"></path>',
    "PR": '<path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"></path>',
    "ISSUE": '<path fill-rule="evenodd" d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"></path>',
    "REPOS": '<path fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"></path>',
}


def gql(query: str, variables: dict) -> dict:
    """Run a GitHub GraphQL query and return its data payload; raise on HTTP or GraphQL errors."""
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch_data() -> tuple:
    """Fetch the top 5 languages by repo size and the stats rows (stars, commits, PRs, issues, contributed-to)."""
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          nodes {
            stargazerCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges { size node { name } }
            }
          }
        }
        contributionsCollection {
          totalPullRequestContributions
          totalIssueContributions
          totalRepositoriesWithContributedCommits
          contributionYears
        }
      }
    }
    """
    data = gql(query, {"login": USERNAME})["user"]

    total_stars = 0
    lang_bytes = {}
    for repo in data["repositories"]["nodes"]:
        total_stars += repo["stargazerCount"]
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            lang_bytes[name] = lang_bytes.get(name, 0) + edge["size"]

    cc = data["contributionsCollection"]
    total_commits = 0
    total_prs = 0
    total_issues = 0
    for year in cc["contributionYears"]:
        yr_query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              totalCommitContributions
              totalPullRequestContributions
              totalIssueContributions
            }
          }
        }
        """
        yr_data = gql(
            yr_query,
            {
                "login": USERNAME,
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year}-12-31T23:59:59Z",
            },
        )["user"]["contributionsCollection"]
        total_commits += yr_data["totalCommitContributions"]
        total_prs += yr_data["totalPullRequestContributions"]
        total_issues += yr_data["totalIssueContributions"]

    top_langs = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:5]

    try:
        colors = requests.get(
            "https://raw.githubusercontent.com/ozh/github-colors/master/colors.json",
            timeout=15,
        ).json()
    except Exception:
        colors = {}

    lang_data = [
        {"name": name, "value": size, "color": colors.get(name, {}).get("color") or "#8b949e"}
        for name, size in top_langs
    ]
    if not lang_data:
        lang_data = [
            {"name": "There are no", "value": 1, "color": "#586e75"},
            {"name": "repos to show", "value": 1, "color": "#586e75"},
        ]

    stats_data = [
        ("STAR", "Total Stars:", str(total_stars)),
        ("COMMIT", "Total Commits:", str(total_commits)),
        ("PR", "Total PRs:", str(total_prs)),
        ("ISSUE", "Total Issues:", str(total_issues)),
        ("REPOS", "Contributed to:", str(cc["totalRepositoriesWithContributedCommits"])),
    ]
    return lang_data, stats_data


# GitHub returns at most 100 commits per page; stop after this many pages per repo.
MAX_HISTORY_PAGES = 50


def fetch_productive_time() -> list:
    """Return 24 commit counts, one per hour of day (shifted by UTC_OFFSET), for the last year."""
    id_query = """
    query($login: String!) {
      user(login: $login) { id }
    }
    """
    user_id = gql(id_query, {"login": USERNAME})["user"]["id"]

    until = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + datetime.timedelta(days=1)
    since = until.replace(year=until.year - 1)
    until_s, since_s = until.isoformat(), since.isoformat()

    repos_query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          commitContributionsByRepository(maxRepositories: 100) {
            repository { name owner { login } }
          }
        }
      }
    }
    """
    collection = gql(
        repos_query, {"login": USERNAME, "from": since_s, "to": until_s}
    )["user"]["contributionsCollection"]

    history_query = """
    query($owner: String!, $name: String!, $userId: ID!, $since: GitTimestamp!, $until: GitTimestamp!, $after: String) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100, since: $since, until: $until, author: {id: $userId}, after: $after) {
                pageInfo { hasNextPage endCursor }
                nodes { authoredDate }
              }
            }
          }
        }
      }
    }
    """
    chart_data = [0] * 24
    for entry in collection["commitContributionsByRepository"]:
        repo = entry["repository"]
        cursor = None
        for _ in range(MAX_HISTORY_PAGES):
            ref = gql(
                history_query,
                {
                    "owner": repo["owner"]["login"],
                    "name": repo["name"],
                    "userId": user_id,
                    "since": since_s,
                    "until": until_s,
                    "after": cursor,
                },
            )["repository"]["defaultBranchRef"]
            history = ((ref or {}).get("target") or {}).get("history")
            if not history:
                break
            for node in history["nodes"]:
                authored = node["authoredDate"]
                hour = datetime.datetime.fromisoformat(authored.replace("Z", "+00:00")).hour
                chart_data[int((hour + UTC_OFFSET) % 24)] += 1
            if not history["pageInfo"]["hasNextPage"]:
                break
            cursor = history["pageInfo"]["endCursor"]
    return chart_data


def fetch_streak_stats() -> dict:
    """Compute total contributions plus the current and longest streaks with their date ranges."""
    meta_query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        contributionsCollection { contributionYears }
      }
    }
    """
    meta = gql(meta_query, {"login": USERNAME})["user"]
    joined = datetime.datetime.fromisoformat(meta["createdAt"].replace("Z", "+00:00")).date()

    local_today = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=UTC_OFFSET)
    ).date()

    day_map = {}
    for year in meta["contributionsCollection"]["contributionYears"]:
        yr_query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                weeks { contributionDays { date contributionCount } }
              }
            }
          }
        }
        """
        cal = gql(
            yr_query,
            {
                "login": USERNAME,
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year}-12-31T23:59:59Z",
            },
        )["user"]["contributionsCollection"]["contributionCalendar"]
        for week in cal["weeks"]:
            for day in week["contributionDays"]:
                d = datetime.date.fromisoformat(day["date"])
                if d <= local_today:
                    day_map[d] = day["contributionCount"]

    ordered = sorted(day_map.items())
    total = sum(c for _, c in ordered)

    # longest streak: max run of consecutive days with count > 0
    longest_len, longest_range = 0, (None, None)
    run_start, run_len = None, 0
    prev_date = None
    for d, c in ordered:
        if c > 0:
            if run_len == 0 or (prev_date and (d - prev_date).days == 1):
                if run_len == 0:
                    run_start = d
                run_len += 1
            else:
                run_start, run_len = d, 1
            if run_len > longest_len:
                longest_len, longest_range = run_len, (run_start, d)
            prev_date = d
        else:
            run_len = 0
            prev_date = d

    # current streak: consecutive days with count > 0 ending today (or yesterday
    # if today has no contribution yet, since today isn't over)
    cur_len, cur_end = 0, None
    for anchor in (local_today, local_today - datetime.timedelta(days=1)):
        if day_map.get(anchor, 0) > 0:
            cur_end = anchor
            break
    if cur_end:
        d = cur_end
        while day_map.get(d, 0) > 0:
            cur_len += 1
            d -= datetime.timedelta(days=1)
        cur_start = cur_end - datetime.timedelta(days=cur_len - 1)
    else:
        cur_start = cur_end = None

    def fmt(d: datetime.date | None) -> str:
        """Format a date such as "Nov 7, 2026", or "-" when there is no date."""
        return f"{d.strftime('%b')} {d.day}, {d.year}" if d else "-"

    return {
        "total": total,
        "total_range": f"{fmt(joined)} - Present",
        "current": cur_len,
        "current_range": f"{fmt(cur_start)} - {fmt(cur_end)}" if cur_end else "-",
        "longest": longest_len,
        "longest_range": f"{fmt(longest_range[0])} - {fmt(longest_range[1])}" if longest_range[0] else "-",
    }


# Colours and font used by the streak stats card.
STREAK_RING = "#58A6FF"
STREAK_FIRE = "#F0883E"
STREAK_CUR_NUM = "#ffffff"
STREAK_CUR_LABEL = "#F0883E"
STREAK_SIDE = "#8B949E"
STREAK_DATES = "#6E7681"
STREAK_FONT = "'Times New Roman', Times, 'Liberation Serif', serif"


def build_streak_card(stats: dict) -> str:
    """Render the streak stats card as an SVG string."""
    width, height = 495, 195
    mid = width / 2

    def side_block(cx: float, num: int, label: str, date_range: str) -> str:
        """Render one side column (number, label, date range) of the streak card."""
        return (
            f'<text x="{cx}" y="80" text-anchor="middle" fill="{STREAK_SIDE}" '
            f'font-family="{STREAK_FONT}" font-weight="700" font-size="34px">{num}</text>'
            f'<text x="{cx}" y="116" text-anchor="middle" fill="{STREAK_SIDE}" '
            f'font-family="{STREAK_FONT}" font-weight="400" font-size="17px">{escape(label)}</text>'
            f'<text x="{cx}" y="146" text-anchor="middle" fill="{STREAK_DATES}" '
            f'font-family="{STREAK_FONT}" font-weight="400" font-size="13px">{escape(date_range)}</text>'
        )

    fire_path = (
        "M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 "
        "L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 "
        "C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 "
        "-0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z"
    )

    body = (
        f'<line x1="165" y1="28" x2="165" y2="170" stroke="{STROKE_COLOR}" stroke-width="1"></line>'
        f'<line x1="330" y1="28" x2="330" y2="170" stroke="{STROKE_COLOR}" stroke-width="1"></line>'
        + side_block(82.5, stats["total"], "Total Contributions", stats["total_range"])
        + f'<circle cx="{mid}" cy="71" r="40" fill="none" stroke="{STREAK_RING}" stroke-width="5"></circle>'
        + f'<g transform="translate({mid},19.5)"><path d="{fire_path}" fill="{STREAK_FIRE}"></path></g>'
        + f'<text x="{mid}" y="80" text-anchor="middle" fill="{STREAK_CUR_NUM}" '
          f'font-family="{STREAK_FONT}" font-weight="700" font-size="34px">{stats["current"]}</text>'
        + f'<text x="{mid}" y="140" text-anchor="middle" fill="{STREAK_CUR_LABEL}" '
          f'font-family="{STREAK_FONT}" font-weight="700" font-size="17px">Current Streak</text>'
        + f'<text x="{mid}" y="166" text-anchor="middle" fill="{STREAK_DATES}" '
          f'font-family="{STREAK_FONT}" font-weight="400" font-size="13px">{escape(stats["current_range"])}</text>'
        + side_block(412.5, stats["longest"], "Longest Streak", stats["longest_range"])
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect x="0.5" y="0.5" rx="4.5" width="{width - 1}" height="{height - 1}" '
        f'fill="{BG_COLOR}" stroke="{STROKE_COLOR}"></rect>'
        f"{body}"
        f"</svg>"
    )


def fetch_daily_contributions(days: int = 31) -> list:
    """Return (day of month, contribution count) pairs for the last `days` days."""
    until = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=1)
    since = until - datetime.timedelta(days=days)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }
    """
    data = gql(
        query,
        {
            "login": USERNAME,
            "from": f"{since.isoformat()}T00:00:00Z",
            "to": f"{until.isoformat()}T00:00:00Z",
        },
    )["user"]["contributionsCollection"]["contributionCalendar"]

    day_map = {}
    for week in data["weeks"]:
        for day in week["contributionDays"]:
            day_map[day["date"]] = day["contributionCount"]

    result = []
    for i in range(days):
        d = since + datetime.timedelta(days=i)
        result.append((d.day, day_map.get(d.isoformat(), 0)))
    return result


def card_shell(title: str, width: int, height: int, body_svg: str) -> str:
    """Wrap body SVG in the shared card frame (background, border and title)."""
    stroke_pct_w = ((width - 2) / width) * 100
    stroke_pct_h = ((height - 2) / height) * 100
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>* {{ font-family: {FONT} }}</style>
<g>
<rect x="1" y="1" rx="5" ry="5" width="{stroke_pct_w}%" height="{stroke_pct_h}%" fill="{BG_COLOR}" stroke="{STROKE_COLOR}" stroke-width="1" stroke-opacity="1"></rect>
<text x="30" y="40" style="font-size:26px;fill:{TITLE_COLOR};">{escape(title)}</text>
<g transform="translate(0,40)">
{body_svg}
</g>
</g>
</svg>'''


def build_stats_card(stats_data: list) -> str:
    """Render the Stats card SVG from (icon, label, value) rows."""
    width, height = 340, 200
    label_h = 16
    rows = []
    for i, (icon_key, name, value) in enumerate(stats_data):
        y = label_h * i * 1.7
        rows.append(
            f'<g transform="translate(0,{y})" fill="{ICON_COLOR}">{ICONS[icon_key]}</g>'
            f'<text x="{label_h * 1.5}" y="{y + label_h}" style="fill:{TEXT_COLOR};font-size:{label_h}px;">{escape(name)}</text>'
            f'<text x="140" y="{y + label_h}" style="fill:{TEXT_COLOR};font-size:{label_h}px;">{escape(value)}</text>'
        )
    logo = f'<g transform="translate(220,20)"><g transform="scale(6)" fill="{ICON_COLOR}">{ICONS["GITHUB"]}</g></g>'
    body = f'<g transform="translate(30,20)">{"".join(rows)}</g>{logo}'
    return card_shell("Stats", width, height, body)


def arc_path(cx: float, cy: float, r_outer: float, r_inner: float, a0: float, a1: float) -> str:
    """Build the SVG path of one donut segment between angles a0 and a1 (radians)."""
    def pt(r: float, a: float) -> tuple:
        """Convert a radius and angle to x/y coordinates around the donut centre."""
        return (cx + r * math.sin(a), cy - r * math.cos(a))

    x1, y1 = pt(r_outer, a0)
    x2, y2 = pt(r_outer, a1)
    x3, y3 = pt(r_inner, a1)
    x4, y4 = pt(r_inner, a0)
    large = 1 if (a1 - a0) > math.pi else 0
    return (
        f"M{x1:.3f},{y1:.3f} A{r_outer:.3f},{r_outer:.3f} 0 {large} 1 {x2:.3f},{y2:.3f} "
        f"L{x3:.3f},{y3:.3f} A{r_inner:.3f},{r_inner:.3f} 0 {large} 0 {x4:.3f},{y4:.3f} Z"
    )


def build_donut_card(lang_data: list) -> str:
    """Render the Top Languages donut card SVG."""
    width, height, x_padding, y_padding = 340, 200, 30, 40
    margin = 10
    radius = (min(width, height) - 2 * margin - y_padding) / 2
    label_h = 15

    total = sum(d["value"] for d in lang_data)
    legend = []
    angle = 0.0
    arcs = []
    for i, d in enumerate(lang_data):
        y = label_h * i * 1.8 + height / 2 - radius - 12
        legend.append(
            f'<rect x="0" y="{y:.2f}" width="{label_h}" height="{label_h}" fill="{d["color"]}" stroke="{BG_COLOR}" stroke-width="1"></rect>'
            f'<text x="{label_h * 1.2}" y="{y + 12:.2f}" style="fill:{TEXT_COLOR};font-size:{label_h}px;">{escape(d["name"])}</text>'
        )
        sweep = (d["value"] / total) * 2 * math.pi if total else 0
        arcs.append(
            f'<path d="{arc_path(0, 0, radius - 10, radius / 2, angle, angle + sweep)}" fill="{d["color"]}" stroke="{BG_COLOR}" stroke-width="2"></path>'
        )
        angle += sweep

    legend_panel = f'<g transform="translate({x_padding + margin},0)">{"".join(legend)}</g>'
    pie_cx = width - radius - margin - x_padding
    pie_cy = (height - y_padding) / 2
    pie_panel = f'<g transform="translate({pie_cx},{pie_cy})">{"".join(arcs)}</g>'
    body = legend_panel + pie_panel
    return card_shell("Top Languages by Repo", width, height, body)


CHART_COLOR = "#BC8CFF"


def build_productive_time_card(chart_data: list, utc_offset: float) -> str:
    """Render the commits-per-hour bar chart card SVG."""
    width, height, x_padding, y_padding = 340, 200, 30, 40
    chart_width = width - 60
    chart_height = 100
    n = 24
    padding = 0.1

    step = chart_width / max(1, n - padding + padding * 2)
    bandwidth = step * (1 - padding)
    start_adj = (chart_width - step * (n - padding)) * 0.5

    def band_x(i: int) -> float:
        """Return the left x position of the bar for hour index i."""
        return start_adj + step * i

    y_max = max(max(chart_data), 1)

    def y(v: float) -> float:
        """Map a commit count to its y position on the chart."""
        return chart_height - (v / y_max) * chart_height

    bars = []
    for i, v in enumerate(chart_data):
        by = y(v)
        bars.append(
            f'<rect x="{band_x(i):.2f}" y="{by:.2f}" width="{bandwidth:.2f}" height="{chart_height - by:.2f}" fill="{CHART_COLOR}"></rect>'
        )

    ticks = []
    for h in (0, 6, 12, 18, 23):
        tx = band_x(h) + bandwidth / 2
        ticks.append(
            f'<line x1="{tx:.2f}" y1="{chart_height}" x2="{tx:.2f}" y2="{chart_height + 6}" stroke="{TEXT_COLOR}"></line>'
            f'<text x="{tx:.2f}" y="{chart_height + 20}" text-anchor="middle" style="fill:{TEXT_COLOR};font-size:12px;">{h}</text>'
        )
    x_axis_line = f'<line x1="0" y1="{chart_height}" x2="{chart_width}" y2="{chart_height}" stroke="{TEXT_COLOR}"></line>'

    y_ticks = []
    for i in range(6):
        v = y_max * i / 5
        ty = y(v)
        y_ticks.append(
            f'<line x1="-6" y1="{ty:.2f}" x2="0" y2="{ty:.2f}" stroke="{TEXT_COLOR}"></line>'
            f'<text x="-10" y="{ty + 4:.2f}" text-anchor="end" style="fill:{TEXT_COLOR};font-size:12px;">{round(v)}</text>'
        )
    y_axis_line = f'<line x1="0" y1="0" x2="0" y2="{chart_height}" stroke="{TEXT_COLOR}"></line>'

    label = f'<text x="220" y="130" style="fill:{TEXT_COLOR};font-size:12px;">per day hour</text>'

    chart_panel = (
        f'<g transform="translate({(width - chart_width) / 2 + 5},{y_padding / 2})">'
        f"{''.join(bars)}{x_axis_line}{''.join(ticks)}{y_axis_line}{''.join(y_ticks)}{label}"
        f"</g>"
    )
    sign = "+" if utc_offset >= 0 else ""
    title = f"Commits (UTC {sign}{utc_offset:.2f})"
    return card_shell(title, width, height, chart_panel)


ACTIVITY_LINE = "#39D0D8"
ACTIVITY_AREA = "#14505A"
ACTIVITY_POINT = "#ffffff"
ACTIVITY_TITLE = "#39D0D8"


def build_activity_graph(daily: list) -> str:
    """Render the contribution activity line and area graph SVG."""
    width, height = 800, 300
    x_padding, y_padding = 46, 55
    plot_w = width - x_padding - 20
    plot_h = height - y_padding - 60

    values = [v for _, v in daily]
    y_max = max(max(values), 1)
    n = len(daily)
    step_x = plot_w / max(1, n - 1)

    def px(i: int) -> float:
        """Return the x position of the i-th day on the plot."""
        return x_padding + step_x * i

    def py(v: float) -> float:
        """Return the y position of a contribution value on the plot."""
        return y_padding + plot_h - (v / y_max) * plot_h

    points = [(px(i), py(v)) for i, (_, v) in enumerate(daily)]

    line_d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)
    area_d = (
        line_d
        + f" L{points[-1][0]:.2f},{y_padding + plot_h:.2f}"
        + f" L{points[0][0]:.2f},{y_padding + plot_h:.2f} Z"
    )

    grid = []
    y_ticks = []
    for i in range(5):
        v = y_max * i / 4
        gy = py(v)
        grid.append(
            f'<line x1="{x_padding}" y1="{gy:.2f}" x2="{x_padding + plot_w}" y2="{gy:.2f}" '
            f'stroke="{STROKE_COLOR}" stroke-dasharray="2,2"></line>'
        )
        y_ticks.append(
            f'<text x="{x_padding - 8}" y="{gy + 3:.2f}" text-anchor="end" '
            f'style="fill:{TEXT_COLOR};font-size:12px;">{round(v)}</text>'
        )

    x_labels = [
        f'<text x="{px(i):.2f}" y="{y_padding + plot_h + 16}" text-anchor="middle" '
        f'style="fill:{TEXT_COLOR};font-size:11px;">{day}</text>'
        for i, (day, _) in enumerate(daily)
    ]

    dots = [
        f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.5" fill="{ACTIVITY_POINT}"></circle>'
        for x, y in points
    ]

    axis_labels = (
        f'<text x="{x_padding + plot_w / 2:.2f}" y="{height - 10}" text-anchor="middle" '
        f'style="fill:{ACTIVITY_TITLE};font-size:13px;">Days</text>'
        f'<text x="14" y="{y_padding + plot_h / 2:.2f}" text-anchor="middle" '
        f'transform="rotate(-90,14,{y_padding + plot_h / 2:.2f})" '
        f'style="fill:{TEXT_COLOR};font-size:12px;">Contributions</text>'
    )

    body = (
        f'<g transform="translate(0,-40)">'
        f"{''.join(grid)}"
        f'<path d="{area_d}" fill="{ACTIVITY_AREA}" fill-opacity="0.55" stroke="none"></path>'
        f'<path d="{line_d}" fill="none" stroke="{ACTIVITY_LINE}" stroke-width="2"></path>'
        f"{''.join(dots)}"
        f"{''.join(y_ticks)}"
        f"{''.join(x_labels)}"
        f"{axis_labels}"
        f"</g>"
    )
    svg = card_shell("Contribution Activity", width, height, body)
    return svg.replace(f'fill:{TITLE_COLOR}', f'fill:{ACTIVITY_TITLE}')


RECENT_START = "<!-- RECENT_PROJECTS:START -->"
RECENT_END = "<!-- RECENT_PROJECTS:END -->"
MAX_DESCRIPTION = 110  # keep the project cards compact
# Course-style prefixes such as "PH_B-14_A08 - " in front of a description.
TITLE_PREFIX = re.compile(r"^\S*\d\S*\s+[-\u2013\u2014:]\s+")


def split_project_text(repo: dict) -> tuple:
    """Return (title, summary) for a repo, turning 'PH_B-14_A08 - Name: text' style descriptions into a clean name and summary."""
    text = TITLE_PREFIX.sub("", (repo.get("description") or "").strip())
    named = re.match(r"^([^:]{2,32}):\s+(.+)$", text)
    if named:
        return named.group(1).strip(), named.group(2).strip()
    quoted = re.search(r'["\u201c]([^"\u201d]{2,32})["\u201d]', text)
    if quoted:
        return quoted.group(1).strip(), text
    pretty = re.sub(r"[-_]+", " ", repo["name"]).strip().title()
    return pretty, text or "No description yet."


def fetch_recent_repos(limit: int = 6) -> list:
    """Return the most recently pushed public, non-fork repositories, without the profile repo itself."""
    query = """
    query($login: String!, $limit: Int!) {
      user(login: $login) {
        repositories(first: $limit, privacy: PUBLIC, isFork: false, ownerAffiliations: OWNER,
                     orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            url
            description
            stargazerCount
            pushedAt
            homepageUrl
            primaryLanguage { name }
            repositoryTopics(first: 4) { nodes { topic { name } } }
          }
        }
      }
    }
    """
    nodes = gql(query, {"login": USERNAME, "limit": limit + 1})["user"]["repositories"]["nodes"]
    return [repo for repo in nodes if repo["name"].lower() != USERNAME.lower()][:limit]


def render_project_card(repo: dict) -> str:
    """Render one repository as a table cell: title, repo name, summary, tags and links."""
    quote = {'"': "&quot;"}
    title, summary = split_project_text(repo)
    summary = summary[:1].upper() + summary[1:]
    if len(summary) > MAX_DESCRIPTION:
        cut = summary[: MAX_DESCRIPTION - 1]
        cut = cut.rsplit(" ", 1)[0] if " " in cut else cut
        summary = cut.rstrip(" ,;:-") + "\u2026"
    pushed =datetime.datetime.fromisoformat(repo["pushedAt"].replace("Z", "+00:00"))
    updated = f"Updated {pushed.strftime('%b')} {pushed.day}, {pushed.year}"
    tags = []
    language = (repo.get("primaryLanguage") or {}).get("name")
    if language:
        tags.append(language)
    topics = (repo.get("repositoryTopics") or {}).get("nodes") or []
    tags += [node["topic"]["name"] for node in topics]
    tags = list(dict.fromkeys(tags))[:4]
    chips = " ".join(f"<code>{escape(tag)}</code>" for tag in tags)
    url = escape(repo["url"], quote)
    links = []
    homepage = (repo.get("homepageUrl") or "").strip()
    if homepage.startswith(("http://", "https://")):
        links.append(f'<a href="{escape(homepage, quote)}">Live demo</a>')
    links.append(f'<a href="{url}">Source code</a>')
    meta = [f"<code>{escape(repo['name'])}</code>", updated]
    if repo.get("stargazerCount"):
        meta.append(f"\u2605 {repo['stargazerCount']}")
    meta_text = " \u00b7 ".join(meta)
    link_text = " \u00b7 ".join(links)
    lines = [
        '<td width="33%" valign="top" align="left">',
        f'<b><a href="{url}">{escape(title)}</a></b>',
        f"<br /><sub>{meta_text}</sub>",
        f"<br /><br /><sub>{escape(summary)}</sub>",
    ]
    if chips:
        lines.append(f"<br /><br />{chips}")
    lines.append(f"<br /><br /><sub>{link_text}</sub>")
    lines.append("</td>")
    return "\n".join(lines)


def render_recent_repos(repos: list) -> str:
    """Render repositories as the HTML table placed between the README markers."""
    if not repos:
        return "<sub>No public repositories to show yet.</sub>"
    cells = [render_project_card(repo) for repo in repos]
    rows = []
    for start in range(0, len(cells), 3):
        row = cells[start : start + 3]
        row += ['<td width="33%"></td>'] * (3 - len(row))
        rows.append("<tr>\n" + "\n".join(row) + "\n</tr>")
    return '<table align="center">\n' + "\n".join(rows) + "\n</table>"


def update_readme(block: str, path: str = "README.md") -> bool:
    """Replace the text between the RECENT_PROJECTS markers; return True when the file changed."""
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    start, end = text.find(RECENT_START), text.find(RECENT_END)
    if start == -1 or end == -1 or end < start:
        return False
    newline = "\r\n" if "\r\n" in text else "\n"
    updated = (
        text[: start + len(RECENT_START)]
        + newline
        + block.replace("\n", newline)
        + newline
        + text[end:]
    )
    if updated == text:
        return False
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(updated)
    return True


def write_card(name: str, build) -> bool:
    """Build one card and write it to assets/; keep the previous file and return False on failure."""
    try:
        svg = build()
    except Exception as error:
        print(f"{name}: failed, keeping the previous file: {error}", file=sys.stderr)
        return False
    with open(f"assets/{name}", "w", encoding="utf-8") as f:
        f.write(svg)
    return True


def main() -> None:
    """Fetch all data and write the generated SVG cards into assets/; one failing card does not stop the rest."""
    os.makedirs("assets", exist_ok=True)
    results = []
    try:
        lang_data, stats_data = fetch_data()
    except Exception as error:
        print(f"fetch_data failed, keeping the previous language and stats cards: {error}", file=sys.stderr)
        results += [False, False]
    else:
        results.append(write_card("top-languages.svg", lambda: build_donut_card(lang_data)))
        results.append(write_card("commit-stats.svg", lambda: build_stats_card(stats_data)))
    results.append(
        write_card(
            "productive-time.svg",
            lambda: build_productive_time_card(fetch_productive_time(), UTC_OFFSET),
        )
    )
    results.append(
        write_card("contribution-activity.svg", lambda: build_activity_graph(fetch_daily_contributions(31)))
    )
    results.append(write_card("streak-stats.svg", lambda: build_streak_card(fetch_streak_stats())))
    if not any(results):
        raise RuntimeError("every card failed")
    try:
        update_readme(render_recent_repos(fetch_recent_repos()))
    except Exception as error:
        print(f"recent projects: failed, keeping the previous section: {error}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"generate_profile_cards.py failed: {e}", file=sys.stderr)
        sys.exit(1)

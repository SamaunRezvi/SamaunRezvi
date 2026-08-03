"""
Self-hosted, byte-for-byte reproduction of the old
github-profile-summary-cards "Top Languages by Repo" (donut chart) and
"Stats" cards. The public github-profile-summary-cards.vercel.app API
that used to render these is permanently dead (crashes with
FUNCTION_INVOCATION_FAILED on every endpoint), so this script recreates
the exact same layout/colours from that project's open-source templates
and writes static SVGs into assets/, refreshed daily by a workflow.
"""
import math
import os
import sys
from xml.sax.saxutils import escape

import requests

USERNAME = os.environ.get("USERNAME", "SamaunRezvi")
TOKEN = os.environ["GITHUB_TOKEN"]

# github_dark theme, taken from github-profile-summary-cards src/const/theme.ts
TITLE_COLOR = "#0366d6"
TEXT_COLOR = "#77909c"
BG_COLOR = "#0d1117"
STROKE_COLOR = "#2e343b"
ICON_COLOR = "#8b949e"
FONT = "'Segoe UI', Ubuntu, \"Helvetica Neue\", Sans-Serif"

ICONS = {
    "GITHUB": '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>',
    "STAR": '<path fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 01-.564-.41L8 2.694v.001z"></path>',
    "COMMIT": '<path fill-rule="evenodd" d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.001 4.001 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z"></path>',
    "PR": '<path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"></path>',
    "ISSUE": '<path fill-rule="evenodd" d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"></path>',
    "REPOS": '<path fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"></path>',
}


def gql(query, variables):
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


def fetch_data():
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
    for year in cc["contributionYears"]:
        yr_query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              totalCommitContributions
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
        ("PR", "Total PRs:", str(cc["totalPullRequestContributions"])),
        ("ISSUE", "Total Issues:", str(cc["totalIssueContributions"])),
        ("REPOS", "Contributed to:", str(cc["totalRepositoriesWithContributedCommits"])),
    ]
    return lang_data, stats_data


def card_shell(title, width, height, body_svg):
    stroke_pct_w = ((width - 2) / width) * 100
    stroke_pct_h = ((height - 2) / height) * 100
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>* {{ font-family: {FONT} }}</style>
<g>
<rect x="1" y="1" rx="5" ry="5" width="{stroke_pct_w}%" height="{stroke_pct_h}%" fill="{BG_COLOR}" stroke="{STROKE_COLOR}" stroke-width="1" stroke-opacity="1"></rect>
<text x="30" y="40" style="font-size:22px;fill:{TITLE_COLOR};">{escape(title)}</text>
<g transform="translate(0,40)">
{body_svg}
</g>
</g>
</svg>'''


def build_stats_card(stats_data):
    width, height = 340, 200
    label_h = 14
    rows = []
    for i, (icon_key, name, value) in enumerate(stats_data):
        y = label_h * i * 1.8
        rows.append(
            f'<g transform="translate(0,{y})" fill="{ICON_COLOR}">{ICONS[icon_key]}</g>'
            f'<text x="{label_h * 1.5}" y="{y + label_h}" style="fill:{TEXT_COLOR};font-size:{label_h}px;">{escape(name)}</text>'
            f'<text x="130" y="{y + label_h}" style="fill:{TEXT_COLOR};font-size:{label_h}px;">{escape(value)}</text>'
        )
    logo = f'<g transform="translate(220,20)"><g transform="scale(6)" fill="{ICON_COLOR}">{ICONS["GITHUB"]}</g></g>'
    body = f'<g transform="translate(30,20)">{"".join(rows)}</g>{logo}'
    return card_shell("Stats", width, height, body)


def arc_path(cx, cy, r_outer, r_inner, a0, a1):
    def pt(r, a):
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


def build_donut_card(lang_data):
    width, height, x_padding, y_padding = 340, 200, 30, 40
    margin = 10
    radius = (min(width, height) - 2 * margin - y_padding) / 2
    label_h = 14

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


def main():
    lang_data, stats_data = fetch_data()
    os.makedirs("assets", exist_ok=True)
    with open("assets/top-languages.svg", "w", encoding="utf-8") as f:
        f.write(build_donut_card(lang_data))
    with open("assets/commit-stats.svg", "w", encoding="utf-8") as f:
        f.write(build_stats_card(stats_data))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"generate_profile_cards.py failed: {e}", file=sys.stderr)
        sys.exit(1)

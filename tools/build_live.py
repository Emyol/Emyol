"""Daily job: fetch public GitHub data, render the `gh stats` panel, refresh the README's recent block.

Everything is built and validated in memory first. Files are written only if every step succeeds.
Run: GITHUB_TOKEN=... python tools/build_live.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

from github_api import GitHubError, fetch_profile
from stats import (MANILA, Commit, StatsView, language_share, recent_commits, recent_lines,
                   replace_block, streaks)
from svg import PALETTES, ROOT, THEMES, WIDTH, document, rect, text, text_width, validate
from term import (CHROME_H, MOTION_CSS, SIZE_BODY, SIZE_SECONDARY, SIZE_SMALL, prompt_line, rise,
                  window)

LOGIN = 'Emyol'
PROFILE_REPO = 'Emyol/Emyol'
LIVE = ROOT / 'assets' / 'live'
VALUE_X = 420


def days(n: int) -> str:
    return f'{n} day' if n == 1 else f'{n} days'


def summarize(user: dict, today: date) -> tuple[StatsView, list[Commit]]:
    calendar = [(date.fromisoformat(d['date']), d['contributionCount'])
                for week in user['calendar']['contributionCalendar']['weeks']
                for d in week['contributionDays']]
    current, longest = streaks(calendar, today)
    view = StatsView(
        year=today.year,
        contributions_this_year=user['thisYear']['contributionCalendar']['totalContributions'],
        current_streak=current,
        longest_streak=longest,
        public_repos=user['owned']['totalCount'],
        languages=language_share(user['owned']['nodes']),
    )
    return view, recent_commits(user['recent']['nodes'], LOGIN, PROFILE_REPO)


def stats_panel(view: StatsView, theme: str) -> str:
    p = PALETTES[theme]
    y = CHROME_H + 62
    body = prompt_line(f'gh stats --user {LOGIN}', 48, y, p)
    rows = [
        (f'contributions ({view.year})', f'{view.contributions_this_year:,}'),
        ('current streak', days(view.current_streak)),
        ('longest streak', days(view.longest_streak)),
        ('public repos', f'{view.public_repos:,}'),
    ]
    y += 30
    for i, (label, value) in enumerate(rows):
        y += 46
        body += rise(text(label, 48, y, SIZE_SECONDARY, p['dim'])
                     + text(value, VALUE_X, y, SIZE_BODY, p['fg'], weight=700), 150 + i * 60)
    y += 60
    lang = text('languages', 48, y, SIZE_SECONDARY, p['dim'])
    end_y = y
    if view.languages:
        colors = [p['heat'][4], p['heat'][3], p['heat'][2], p['string'], p['heat'][1], p['dim']]
        bar_w = WIDTH - 40 - VALUE_X
        x = VALUE_X
        for i, ((_, pct), color) in enumerate(zip(view.languages, colors)):
            w = (VALUE_X + bar_w - x) if i == len(view.languages) - 1 else round(bar_w * pct / 100)
            lang += rect(x, y - 18, w, 18, color)
            x += w
        x, end_y = VALUE_X, y + 46
        for (name, pct), color in zip(view.languages, colors):
            label = f'{name} {pct}%'
            w = 24 + text_width(label, SIZE_SMALL) + 28
            if x > VALUE_X and x + w > WIDTH - 40:
                x, end_y = VALUE_X, end_y + 36
            lang += rect(x, end_y - 15, 14, 14, color, 3) + text(label, x + 24, end_y, SIZE_SMALL, p['fg'])
            x += w
    else:
        lang += text('no language data yet', VALUE_X, y, SIZE_SECONDARY, p['dim'])
    body += rise(lang, 150 + len(rows) * 60)
    height = int(end_y + 40)
    share = ', '.join(f'{n} {pct}%' for n, pct in view.languages) or 'none yet'
    title = (f'GitHub stats for {LOGIN}: {view.contributions_this_year:,} contributions in {view.year}, '
             f'current streak {days(view.current_streak)}, longest streak {days(view.longest_streak)}, '
             f'{view.public_repos} public repositories. Languages: {share}.')
    return document(height, title, window(height, 'gh stats', body, p), MOTION_CSS)


def render(user: dict, today: date, readme: str) -> tuple[dict[str, str], str]:
    view, commits = summarize(user, today)
    svgs = {f'stats-{theme}.svg': stats_panel(view, theme) for theme in THEMES}
    for svg in svgs.values():
        validate(svg)
    return svgs, replace_block(readme, recent_lines(commits))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Refresh the live stats panel and recent commits.')
    parser.add_argument('--fixture', type=Path, help='read the GraphQL user object from JSON (tests only)')
    parser.add_argument('--readme', type=Path, default=ROOT / 'README.md')
    parser.add_argument('--out', type=Path, default=LIVE)
    parser.add_argument('--today', type=date.fromisoformat, help='override today (YYYY-MM-DD, Manila)')
    args = parser.parse_args(argv)
    now = datetime.now(MANILA)
    today = args.today or now.date()
    try:
        if args.fixture:
            user = json.loads(args.fixture.read_text(encoding='utf-8'))
        else:
            user = fetch_profile(LOGIN, os.environ['GITHUB_TOKEN'], now)
        svgs, readme = render(user, today, args.readme.read_text(encoding='utf-8'))
    except (GitHubError, KeyError, TypeError, ValueError, ET.ParseError, OSError) as exc:
        print(f'build_live: nothing written: {exc!r}', file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    for name, svg in svgs.items():
        (args.out / name).write_text(svg, encoding='utf-8', newline='\n')
    args.readme.write_text(readme, encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

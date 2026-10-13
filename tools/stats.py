"""Pure logic behind the daily live section: streaks, language share, recent commits."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta, timezone
from typing import Iterable

MANILA = timezone(timedelta(hours=8))
START = '<!-- recent:start -->'
END = '<!-- recent:end -->'
MAX_MESSAGE = 72
_MD_SPECIAL = set('\\`*_[]()#|~!')


@dataclass(frozen=True)
class StatsView:
    year: int
    contributions_this_year: int
    current_streak: int
    longest_streak: int
    public_repos: int
    languages: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Commit:
    sha7: str
    repo: str
    message: str
    url: str
    when: str


def streaks(days: Iterable[tuple[date, int]], today: date) -> tuple[int, int]:
    """(current, longest). An empty today does not break a streak that ran through yesterday."""
    active = {day for day, count in days if count > 0}
    longest = run = 0
    previous = None
    for day in sorted(active):
        run = run + 1 if previous == day - timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    cursor = today if today in active else today - timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def language_share(repos: Iterable[dict], top: int = 5) -> tuple[tuple[str, int], ...]:
    """Top languages by bytes across non-fork repos, as whole percentages summing to 100."""
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get('isFork'):
            continue
        for edge in repo['languages']['edges']:
            name = edge['node']['name']
            totals[name] = totals.get(name, 0) + edge['size']
    grand = sum(totals.values())
    if not grand:
        return ()
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    buckets = ranked[:top]
    rest = sum(size for _, size in ranked[top:])
    if rest:
        buckets.append(('Other', rest))
    exact = [size * 100 / grand for _, size in buckets]
    percents = [int(v) for v in exact]
    order = sorted(range(len(exact)), key=lambda i: exact[i] - percents[i], reverse=True)
    for i in order[:100 - sum(percents)]:
        percents[i] += 1
    return tuple((name, pct) for (name, _), pct in zip(buckets, percents) if pct > 0)


def recent_commits(repos: Iterable[dict], login: str, exclude: str, limit: int = 3) -> list[Commit]:
    found = []
    for repo in repos:
        if repo['nameWithOwner'].lower() == exclude.lower() or not repo.get('defaultBranchRef'):
            continue
        for node in repo['defaultBranchRef']['target']['history']['nodes']:
            author = (node.get('author') or {}).get('user') or {}
            if author.get('login') != login or node['messageHeadline'].startswith('Merge'):
                continue
            found.append(Commit(node['oid'][:7], repo['name'], node['messageHeadline'],
                                node['url'], node['committedDate']))
    found.sort(key=lambda c: c.when, reverse=True)
    return found[:limit]


def escape_markdown(value: str) -> str:
    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return ''.join('\\' + ch if ch in _MD_SPECIAL else ch for ch in value)


def shorten(value: str, limit: int = MAX_MESSAGE) -> str:
    return value if len(value) <= limit else value[:limit - 1].rstrip() + '…'


def recent_lines(commits: list[Commit]) -> list[str]:
    if not commits:
        return ['- _No recent public commits._']
    return [f'- [`{c.sha7}`]({c.url}) **{escape_markdown(c.repo)}**: {escape_markdown(shorten(c.message))}'
            for c in commits]


def replace_block(readme: str, lines: list[str]) -> str:
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError('README needs exactly one recent:start and one recent:end marker')
    if readme.index(END) < readme.index(START):
        raise ValueError('recent:end comes before recent:start')
    head, rest = readme.split(START)
    tail = rest.split(END)[1]
    return f'{head}{START}\n' + '\n'.join(lines) + f'\n{END}{tail}'

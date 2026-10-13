"""One GraphQL round-trip for everything the live section needs (public data only)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime

API = 'https://api.github.com/graphql'

QUERY = """
query($login: String!, $yearStart: DateTime!) {
  user(login: $login) {
    thisYear: contributionsCollection(from: $yearStart) { contributionCalendar { totalContributions } }
    calendar: contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
    owned: repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { isFork languages(first: 20, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
    recent: repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 6,
                         orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name nameWithOwner
        defaultBranchRef { target { ... on Commit { history(first: 5) {
          nodes { oid messageHeadline committedDate url author { user { login } } }
        } } } }
      }
    }
  }
}
"""


class GitHubError(RuntimeError):
    pass


def fetch_profile(login: str, token: str, now: datetime, opener=urllib.request.urlopen) -> dict:
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    body = json.dumps({'query': QUERY, 'variables': {'login': login, 'yearStart': year_start.isoformat()}})
    request = urllib.request.Request(API, data=body.encode(), headers={
        'Authorization': f'bearer {token}', 'Content-Type': 'application/json',
        'User-Agent': f'{login}-profile-readme'})
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        raise GitHubError(f'GitHub request failed: {exc.reason}') from exc
    if payload.get('errors'):
        raise GitHubError('GitHub GraphQL errors: ' + '; '.join(e.get('message', '?') for e in payload['errors']))
    user = (payload.get('data') or {}).get('user')
    if not user:
        raise GitHubError(f'user {login} not found')
    return user

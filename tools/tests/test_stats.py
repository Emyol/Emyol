from datetime import date, timedelta

import pytest

from stats import (END, START, Commit, escape_markdown, language_share, recent_commits,
                   recent_lines, replace_block, shorten, streaks)

TODAY = date(2026, 10, 13)


def run(counts, end=TODAY):
    """counts[-1] is `end`, counts[-2] the day before, and so on."""
    return [(end - timedelta(days=len(counts) - 1 - i), c) for i, c in enumerate(counts)]


def test_streak_counts_consecutive_days_ending_today():
    assert streaks(run([0, 2, 1, 4]), TODAY) == (3, 3)


def test_streak_survives_an_empty_today():
    assert streaks(run([1, 1, 0]), TODAY) == (2, 2)


def test_streak_zero_when_today_and_yesterday_empty():
    assert streaks(run([5, 0, 0]), TODAY) == (0, 1)


def test_longest_streak_spans_gaps_correctly():
    assert streaks(run([1, 1, 1, 1, 0, 1]), TODAY) == (1, 4)


def test_streak_crosses_the_year_boundary():
    jan1 = date(2027, 1, 1)
    assert streaks(run([1, 1, 1], end=jan1), jan1) == (3, 3)


def test_streak_of_nothing():
    assert streaks([], TODAY) == (0, 0)


def lang_repo(*pairs, fork=False):
    return {'isFork': fork, 'languages': {'edges': [{'size': s, 'node': {'name': n}} for n, s in pairs]}}


def test_language_share_sums_to_100_with_equal_thirds():
    assert language_share([lang_repo(('A', 1), ('B', 1), ('C', 1))]) == (('A', 34), ('B', 33), ('C', 33))


def test_language_share_excludes_forks_and_buckets_other():
    repos = [lang_repo(('TypeScript', 6000), ('CSS', 500)), lang_repo(('Python', 3000)),
             lang_repo(('Dart', 1500)), lang_repo(('JavaScript', 1000), ('HTML', 400)),
             lang_repo(('C++', 300)), lang_repo(('Rust', 99999), fork=True)]
    assert language_share(repos) == (('TypeScript', 47), ('Python', 24), ('Dart', 12),
                                     ('JavaScript', 8), ('CSS', 4), ('Other', 5))


def test_language_share_empty():
    assert language_share([lang_repo()]) == ()


def commit(oid, msg, when, login='Emyol'):
    return {'oid': oid, 'messageHeadline': msg, 'committedDate': when, 'url': f'https://x/{oid}',
            'author': {'user': {'login': login} if login else None}}


def repo(name, *commits, owner='Emyol'):
    ref = {'target': {'history': {'nodes': list(commits)}}} if commits else None
    return {'name': name, 'nameWithOwner': f'{owner}/{name}', 'defaultBranchRef': ref}


def test_recent_commits_filters_and_sorts():
    repos = [
        repo('pane', commit('a' * 40, 'add grid', '2026-10-12T10:00:00Z'),
             commit('b' * 40, 'Merge branch main', '2026-10-12T11:00:00Z')),
        repo('Emyol', commit('c' * 40, 'chore: refresh', '2026-10-13T00:00:00Z')),
        repo('site', commit('d' * 40, 'polish', '2026-10-11T09:00:00Z'),
             commit('e' * 40, 'deps: bump', '2026-10-12T12:00:00Z', login='dependabot[bot]'),
             commit('f' * 40, 'bot commit', '2026-10-12T13:00:00Z', login=None)),
        repo('empty'),
        repo('old', commit('9' * 40, 'older', '2026-09-01T00:00:00Z')),
    ]
    got = recent_commits(repos, 'Emyol', 'Emyol/Emyol')
    assert [(c.sha7, c.repo) for c in got] == [('aaaaaaa', 'pane'), ('ddddddd', 'site'), ('9999999', 'old')]


def test_recent_lines_escape_markup():
    line = recent_lines([Commit('abc1234', 'my_repo', 'hero <script> & *bold* `x` [y](z)', 'https://u', '')])[0]
    assert line == ('- [`abc1234`](https://u) **my\\_repo**: hero &lt;script&gt; &amp; '
                    '\\*bold\\* \\`x\\` \\[y\\]\\(z\\)')


def test_recent_lines_truncate_long_messages():
    assert shorten('x' * 100) == 'x' * 71 + '…'
    assert shorten('short') == 'short'
    line = recent_lines([Commit('abc1234', 'r', 'y' * 100, 'https://u', '')])[0]
    assert line.endswith('y' * 71 + '…')


def test_recent_lines_when_nothing_qualifies():
    assert recent_lines([]) == ['- _No recent public commits._']


def test_escape_markdown_leaves_plain_text_alone():
    assert escape_markdown('pane: add grid persistence') == 'pane: add grid persistence'


README = f'# hi\n\n{START}\nold line\n{END}\n\nbye\n'


def test_replace_block_swaps_only_between_markers():
    assert replace_block(README, ['- new']) == f'# hi\n\n{START}\n- new\n{END}\n\nbye\n'


def test_replace_block_is_idempotent():
    once = replace_block(README, ['- a', '- b'])
    assert replace_block(once, ['- a', '- b']) == once


@pytest.mark.parametrize('bad', ['# nothing', f'{START}\n{START}\n{END}', f'{END}\n{START}'])
def test_replace_block_rejects_missing_duplicate_or_reversed_markers(bad):
    with pytest.raises(ValueError):
        replace_block(bad, ['- x'])

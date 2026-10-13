import io
import json
import urllib.error
from datetime import date, datetime
from pathlib import Path

import pytest

import build_live
from github_api import GitHubError, fetch_profile
from stats import END, MANILA, START, StatsView
from svg import PALETTES, validate

FIXTURE = Path(__file__).parent / 'fixtures' / 'user.json'
README = f'# hi\n{START}\nold\n{END}\nbye\n'
NOW = datetime(2026, 10, 13, 9, tzinfo=MANILA)


def run(tmp_path, readme=README, fixture=FIXTURE, extra=()):
    readme_path = tmp_path / 'README.md'
    readme_path.write_text(readme, encoding='utf-8')
    out = tmp_path / 'live'
    args = ['--readme', str(readme_path), '--out', str(out), '--today', '2026-10-13', *extra]
    if fixture is not None:
        args = ['--fixture', str(fixture), *args]
    return build_live.main(args), readme_path, out


def test_fixture_run_writes_both_themes_and_readme(tmp_path):
    code, readme, out = run(tmp_path)
    assert code == 0
    assert sorted(p.name for p in out.iterdir()) == ['stats-dark.svg', 'stats-light.svg']
    text = readme.read_text(encoding='utf-8')
    assert text.startswith('# hi\n') and text.endswith('bye\n') and 'old' not in text
    assert '**pane**: pane: add widget grid persistence' in text
    assert '&lt;polish&gt; &amp; \\*tweaks\\*' in text
    assert 'refresh live profile data' not in text and 'Merge' not in text


def test_stats_numbers_come_from_the_data(tmp_path):
    _, _, out = run(tmp_path)
    svg = (out / 'stats-dark.svg').read_text(encoding='utf-8')
    for label in ['142', '3 days', '4 days', '16', 'TypeScript 47%', 'Other 5%']:
        assert f'aria-label="{label}"' in svg, label
    lowered = svg.lower()
    assert 'followers' not in lowered and 'stars' not in lowered


def test_missing_markers_write_nothing(tmp_path):
    code, readme, out = run(tmp_path, readme='# no markers\n')
    assert code == 1
    assert readme.read_text(encoding='utf-8') == '# no markers\n'
    assert not out.exists()


def test_malformed_payload_writes_nothing(tmp_path):
    bad = tmp_path / 'bad.json'
    bad.write_text('{"thisYear": {}}', encoding='utf-8')
    code, readme, out = run(tmp_path, fixture=bad)
    assert code == 1
    assert readme.read_text(encoding='utf-8') == README
    assert not out.exists()


def test_missing_token_fails_cleanly(tmp_path, monkeypatch):
    monkeypatch.delenv('GITHUB_TOKEN', raising=False)
    code, readme, out = run(tmp_path, fixture=None)
    assert code == 1 and not out.exists()


def test_panel_without_languages_is_valid():
    view = StatsView(2026, 0, 0, 0, 0, ())
    svg = build_live.stats_panel(view, 'light')
    validate(svg)
    assert 'aria-label="no language data yet"' in svg
    assert 'aria-label="0 days"' in svg


def responder(payload):
    def opener(request, timeout):
        return io.BytesIO(json.dumps(payload).encode())
    return opener


def test_graphql_errors_raise():
    with pytest.raises(GitHubError, match='rate limited'):
        fetch_profile('Emyol', 't', NOW, opener=responder({'errors': [{'message': 'rate limited'}]}))


def test_http_failure_raises():
    def opener(request, timeout):
        raise urllib.error.URLError('offline')
    with pytest.raises(GitHubError, match='offline'):
        fetch_profile('Emyol', 't', NOW, opener=opener)


def test_null_user_raises():
    with pytest.raises(GitHubError, match='not found'):
        fetch_profile('Emyol', 't', NOW, opener=responder({'data': {'user': None}}))


def test_request_sends_token_and_manila_year_start():
    seen = {}

    def opener(request, timeout):
        seen['auth'] = request.get_header('Authorization')
        seen['body'] = json.loads(request.data)
        return io.BytesIO(json.dumps({'data': {'user': {'ok': 1}}}).encode())

    assert fetch_profile('Emyol', 'tok', NOW, opener=opener) == {'ok': 1}
    assert seen['auth'] == 'bearer tok'
    assert seen['body']['variables'] == {'login': 'Emyol', 'yearStart': '2026-01-01T00:00:00+08:00'}


def _luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize('theme', ['dark', 'light'])
def test_language_series_colors_are_visible_and_distinct(theme):
    colors = build_live.SERIES[theme]
    assert len(colors) == 6 and len(set(colors)) == 6
    for color in colors:
        assert _contrast(color, PALETTES[theme]['bg']) >= 2.5, color

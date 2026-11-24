from svg import ROOT

WORKFLOW = (ROOT / '.github' / 'workflows' / 'profile.yml').read_text(encoding='utf-8')


def test_runs_daily_at_manila_midnight_and_on_demand():
    assert 'cron: "0 16 * * *"' in WORKFLOW
    assert 'workflow_dispatch:' in WORKFLOW


def test_pins_action_versions():
    for ref in ['actions/checkout@v7', 'actions/setup-python@v7', 'Platane/snk@v3',
                'crazy-max/ghaction-github-pages@v5']:
        assert ref in WORKFLOW


def test_snake_uses_the_dive_palette():
    assert ('dist/github-snake.svg?color_snake=#0058b8&color_dots=#e6e6e2,#a9c6e6,#6f9fd6,#2f74c0,#0058b8'
            in WORKFLOW)
    assert ('dist/github-snake-dark.svg?color_snake=#2997ff&color_dots=#161616,#0b2d4d,#114f87,#1b74c2,#2997ff'
            in WORKFLOW)


def test_commits_only_live_files_and_only_when_changed():
    assert 'python tools/build_live.py' in WORKFLOW
    assert 'git add assets/live README.md' in WORKFLOW
    assert 'git diff --cached --quiet' in WORKFLOW
    assert 'contents: write' in WORKFLOW

from svg import ROOT

WORKFLOW = (ROOT / '.github' / 'workflows' / 'profile.yml').read_text(encoding='utf-8')


def test_runs_daily_at_manila_midnight_and_on_demand():
    assert 'cron: "0 16 * * *"' in WORKFLOW
    assert 'workflow_dispatch:' in WORKFLOW


def test_pins_action_versions():
    for ref in ['actions/checkout@v7', 'actions/setup-python@v7', 'Platane/snk@v3',
                'crazy-max/ghaction-github-pages@v5']:
        assert ref in WORKFLOW


def test_snake_uses_phosphor_palette():
    assert ('dist/github-snake.svg?color_snake=#1f7a43&color_dots=#e3e9e4,#b9dcc4,#7cc296,#3f9a62,#1f7a43'
            in WORKFLOW)
    assert ('dist/github-snake-dark.svg?color_snake=#7ee2a0&color_dots=#141a16,#1d3a28,#2b6a44,#4fa36e,#7ee2a0'
            in WORKFLOW)


def test_commits_only_live_files_and_only_when_changed():
    assert 'python tools/build_live.py' in WORKFLOW
    assert 'git add assets/live README.md' in WORKFLOW
    assert 'git diff --cached --quiet' in WORKFLOW
    assert 'contents: write' in WORKFLOW

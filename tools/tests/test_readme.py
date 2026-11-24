import re

from stats import END, START
from svg import ROOT

README = (ROOT / 'README.md').read_text(encoding='utf-8')


def test_every_local_image_exists():
    paths = re.findall(r'(?:srcset|src)="(assets/[^"]+)"', README)
    assert len(paths) >= 20
    assert [p for p in paths if not (ROOT / p).exists()] == []


def test_every_picture_has_a_dark_source_and_alt_text():
    pictures = re.findall(r'<picture>(.*?)</picture>', README, flags=re.S)
    assert len(pictures) == 7
    for block in pictures:
        assert 'media="(prefers-color-scheme: dark)"' in block
        alt = re.search(r'<img [^>]*alt="([^"]*)"', block)
        assert alt and alt.group(1).strip(), block


def test_recent_markers_appear_once():
    assert README.count(START) == 1 and README.count(END) == 1


def test_contact_links():
    for url in ['https://project-miel.vercel.app', 'https://www.linkedin.com/in/amiel-josiah-acu%C3%B1a-4786a515a',
                'mailto:acunaamieljosiah@gmail.com']:
        assert url in README


def test_hero_and_every_project_card_are_shown():
    import ocean
    assert 'src="assets/dive/hero.svg"' in README
    for item in ocean.PROJECTS:
        assert f'src="assets/dive/work-{item["slug"]}.svg"' in README
        assert f'<a href="{item["code"]}">' in README


def test_old_art_is_gone():
    for old in ['silver-field', 'toolkit.svg', 'assets/kitako.svg', 'assets/static/hero-', '$ whoami']:
        assert old not in README
    assert not (ROOT / 'tools' / 'build_visuals.py').exists()

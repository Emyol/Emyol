import build_static as bs
from svg import PALETTES, missing_glyphs, validate

FILES = bs.build_all()


def test_builds_nine_assets_for_both_themes():
    stems = {name.rsplit('-', 1)[0] for name in FILES}
    assert stems == {'hero', 'work-header', 'work-kitako', 'work-icare', 'work-bekilang',
                     'work-citysense', 'stack', 'graph-header', 'footer'}
    assert len(FILES) == 18


def test_every_asset_is_valid():
    for svg in FILES.values():
        validate(svg)


def test_each_theme_uses_its_own_background():
    assert PALETTES['dark']['bg'] in FILES['hero-dark.svg']
    assert PALETTES['light']['bg'] in FILES['hero-light.svg']
    assert PALETTES['dark']['bg'] not in FILES['hero-light.svg']


def test_hero_reads_as_a_session():
    hero = FILES['hero-dark.svg']
    for label in ['whoami', 'Amiel Acuña', 'cat role.txt', 'FEU Tech']:
        assert f'aria-label="{label}"' in hero
    assert 'class="cursor"' in hero and 'class="type"' in hero


def test_only_the_hero_loops():
    for name, svg in FILES.items():
        if not name.startswith('hero'):
            assert 'class="cursor"' not in svg, name


def test_every_glyph_of_static_copy_exists():
    for family, weight, value in bs.all_copy():
        assert missing_glyphs(value, family, weight) == set(), value


def test_no_hover_affordances():
    assert not any('↗' in svg for svg in FILES.values())


def test_work_strips_name_their_project_and_stagger():
    icare = FILES['work-icare-dark.svg']
    assert 'aria-label="iCARE Reservation"' in icare
    assert '700+ STEM students' in icare
    assert 'animation-delay:180ms' in icare  # index 1 → 120 + 60


def test_stack_lists_every_group_and_tool():
    stack = FILES['stack-dark.svg']
    for key, items in bs.STACK:
        assert f'aria-label="{key}"' in stack
        for _, label in items:
            assert f'aria-label="{label}"' in stack

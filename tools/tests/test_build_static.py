import build_static as bs
from svg import PALETTES, missing_glyphs, validate
from svg import text_width
from term import SIZE_SECONDARY, flow

FILES = bs.build_all()


def test_builds_five_assets_for_both_themes():
    stems = {name.rsplit('-', 1)[0] for name in FILES}
    assert stems == {'work-header', 'stack-header', 'stack', 'graph-header', 'footer'}
    assert len(FILES) == 10


def test_every_asset_is_valid():
    for svg in FILES.values():
        validate(svg)


def test_each_theme_uses_its_own_background():
    assert PALETTES['dark']['bg'] in FILES['stack-dark.svg']
    assert PALETTES['light']['bg'] in FILES['stack-light.svg']
    assert PALETTES['dark']['bg'] not in FILES['stack-light.svg']


def test_headers_are_transparent_depth_marks():
    for stem, (depth, title, _) in bs.HEADERS.items():
        svg = FILES[f'{stem}-dark.svg']
        assert f'aria-label="{depth}"' in svg and f'aria-label="{title}"' in svg
        assert PALETTES['dark']['bg'] not in svg, stem


def test_nothing_static_loops():
    for name, svg in FILES.items():
        assert 'class="cursor"' not in svg, name


def test_every_glyph_of_static_copy_exists():
    for family, weight, value in bs.all_copy():
        assert missing_glyphs(value, family, weight) == set(), value


def test_no_hover_affordances():
    assert not any('↗' in svg for svg in FILES.values())


def test_stack_lists_every_group_and_tool():
    stack = FILES['stack-dark.svg']
    for key, items in bs.STACK:
        assert f'aria-label="{key}"' in stack
        for _, label in items:
            assert f'aria-label="{label}"' in stack


def test_each_stack_group_fits_on_one_row():
    """A lone wrapped item (e.g. 'C++' under Languages) reads as a layout bug."""
    for key, items in bs.STACK:
        _, rows = flow(items, bs.STACK_ITEMS_X, bs.STACK_RIGHT, 0, PALETTES['dark'], gap=bs.STACK_GAP)
        assert rows == 1, key


def test_neofetch_columns_have_breathing_room():
    sun_right = 48 + max(text_width(line, bs.SUN_SIZE) for line in bs.SUN)
    assert sun_right + 16 <= bs.STACK_KEY_X
    widest_key = max(text_width(key, SIZE_SECONDARY, weight=700) for key, _ in bs.STACK)
    assert bs.STACK_KEY_X + widest_key + 16 <= bs.STACK_ITEMS_X


def test_committed_static_assets_match_the_builder():
    """Stale committed art is easy to ship after a shared CSS/layout change; rebuild with build_static.py."""
    stale = [name for name, svg in FILES.items()
             if (bs.STATIC / name).read_text(encoding='utf-8') != svg]
    assert stale == []

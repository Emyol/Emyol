import ocean

FILES = ocean.build_all()


def test_builds_the_hero_and_one_card_per_project():
    assert set(FILES) == {'hero.svg'} | {f"work-{p['slug']}.svg" for p in ocean.PROJECTS}


def test_every_file_is_titled_and_within_budget():
    for name, svg in FILES.items():
        assert '<title>' in svg, name
        assert len(svg.encode('utf-8')) <= ocean.MAX_BYTES, name


def test_hero_keeps_a_still_frame_for_reduced_motion():
    hero = FILES['hero.svg']
    assert 'class="f f0"' in hero and 'class="b b0"' in hero
    assert 'prefers-reduced-motion:reduce' in hero
    assert hero.count('class="f') == 64


def test_text_rows_keep_their_spaces():
    for svg in FILES.values():
        assert 'xml:space="preserve"' in svg


def test_cards_count_down_in_depth():
    assert [ocean.card_depth(i) for i in range(3)] == ['\u221260 m', '\u221280 m', '\u2212100 m']


def test_committed_ocean_assets_match_the_builder():
    stale = [n for n, svg in FILES.items() if (ocean.OUT / n).read_text(encoding='utf-8') != svg]
    assert stale == []

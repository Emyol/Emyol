import xml.etree.ElementTree as ET

import pytest

from svg import PALETTES, THEMES, document, missing_glyphs, rect, text, text_width, validate

NS = '{http://www.w3.org/2000/svg}'


def test_text_escapes_label_and_parses():
    label = 'C++ & <F#>'
    svg = document(100, label, text(label, 10, 50, 26, '#fff'))
    root = ET.fromstring(svg)
    assert root.find(f'{NS}title').text == label
    assert root.find(f'{NS}g').get('aria-label') == label


def test_text_width_grows_with_length_and_size():
    assert text_width('ab', 26) > text_width('a', 26) > 0
    assert text_width('a', 52) == pytest.approx(2 * text_width('a', 26))


def test_mono_glyphs_share_one_advance():
    assert text_width('i', 26) == pytest.approx(text_width('W', 26))
    assert text_width('i', 26) == pytest.approx(0.6 * 26)


def test_unknown_glyph_falls_back_to_question_mark():
    assert missing_glyphs('a一b') == {'一'}
    assert text_width('a一b', 26) == pytest.approx(text_width('a?b', 26))
    text('a一b', 0, 0, 26, '#fff')  # must not raise


def test_sans_bold_has_the_name():
    assert missing_glyphs('Amiel Acuña.', 'sans', 800) == set()


def test_validate_rejects_missing_title():
    with pytest.raises(ValueError, match='title'):
        validate('<svg xmlns="http://www.w3.org/2000/svg"></svg>')


def test_validate_rejects_oversize():
    big = document(10, 't', rect(0, 0, 1, 1, '#000') * 20000)
    with pytest.raises(ValueError, match='bytes'):
        validate(big)


def test_validate_rejects_broken_xml():
    with pytest.raises(ET.ParseError):
        validate('<svg><title>x</title>')


def test_palettes_are_complete_and_parallel():
    assert THEMES == ('dark', 'light')
    assert set(PALETTES['dark']) == set(PALETTES['light']) == {
        'bg', 'chrome', 'fg', 'dim', 'prompt', 'string', 'line', 'heat'}
    assert len(PALETTES['dark']['heat']) == len(PALETTES['light']['heat']) == 5

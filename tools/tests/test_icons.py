import pytest

from svg import ICONS, icon

REQUIRED = [
    'typescript', 'javascript', 'python', 'dart', 'cplusplus', 'nextdotjs', 'react',
    'tailwindcss', 'shadcnui', 'gsap', 'flutter', 'onnx', 'supabase', 'prisma', 'flask',
    'pandas', 'scikitlearn', 'playwright', 'vitest', 'git', 'vercel', 'figma', 'leaflet', 'vite',
]


def test_all_required_icons_are_vendored():
    assert [n for n in REQUIRED if not (ICONS / f'{n}.svg').exists()] == []


def test_simple_icon_scales_24_units_to_requested_size():
    out = icon('react', 10, 20, 48, '#7ee2a0')
    assert 'translate(10.00 20.00) scale(2.00000)' in out
    assert 'fill="#7ee2a0"' in out
    assert '<path d="' in out


def test_devicon_scales_128_units():
    assert 'scale(0.25000)' in icon('playwright', 0, 0, 32, '#000')


def test_icon_strips_titles_and_own_fills():
    out = icon('react', 0, 0, 24, '#123456')
    assert '<title' not in out
    assert out.count('fill=') == 1


def test_missing_icon_names_the_icon():
    with pytest.raises(FileNotFoundError, match='nope'):
        icon('nope', 0, 0, 10, '#000')

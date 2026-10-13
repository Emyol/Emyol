"""Shared SVG primitives for the terminal-style profile artwork.

Text is outlined into <path>s because GitHub shows README images through
<img>, which cannot load web fonts.
"""
from __future__ import annotations

from functools import lru_cache
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
ICONS = TOOLS / 'icons'
FONTS = {
    'sans': TOOLS / 'fonts' / 'Geist[wght].ttf',
    'mono': TOOLS / 'fonts' / 'GeistMono[wght].ttf',
}
WIDTH = 1200
MAX_BYTES = 300_000
THEMES = ('dark', 'light')
EASE_OUT = 'cubic-bezier(.23,1,.32,1)'
SVG_NS = '{http://www.w3.org/2000/svg}'

PALETTES = {
    'dark': {
        'bg': '#0c100e', 'chrome': '#151b17', 'fg': '#d7e4da', 'dim': '#7d8f82',
        'prompt': '#7ee2a0', 'string': '#a8d8ff', 'line': '#223028',
        'heat': ('#141a16', '#1d3a28', '#2b6a44', '#4fa36e', '#7ee2a0'),
    },
    'light': {
        'bg': '#f4f7f4', 'chrome': '#e8eee9', 'fg': '#1d2a21', 'dim': '#5d6e62',
        'prompt': '#1f7a43', 'string': '#0b5cad', 'line': '#cfdcd2',
        'heat': ('#e3e9e4', '#b9dcc4', '#7cc296', '#3f9a62', '#1f7a43'),
    },
}


@lru_cache(maxsize=None)
def _font(family: str, weight: int):
    font = instantiateVariableFont(TTFont(FONTS[family]), {'wght': weight})
    return font, font.getGlyphSet(), font.getBestCmap(), font['head'].unitsPerEm


def _glyph_name(family: str, weight: int, char: str) -> str:
    cmap = _font(family, weight)[2]
    return cmap.get(ord(char)) or cmap[ord('?')]


@lru_cache(maxsize=None)
def _outline(family: str, weight: int, name: str) -> str:
    glyphs = _font(family, weight)[1]
    pen = SVGPathPen(glyphs, ntos=lambda v: f'{v:g}')
    glyphs[name].draw(pen)
    return pen.getCommands()


def missing_glyphs(value: str, family: str = 'mono', weight: int = 400) -> set[str]:
    cmap = _font(family, weight)[2]
    return {char for char in value if ord(char) not in cmap}


def text_width(value: str, size: float, family: str = 'mono', weight: int = 400,
               tracking: float = 0.0) -> float:
    _, glyphs, _, upem = _font(family, weight)
    scale = size / upem
    return sum(glyphs[_glyph_name(family, weight, c)].width * scale + tracking for c in value)


def text(value: str, x: float, y: float, size: float, color: str, family: str = 'mono',
         weight: int = 400, tracking: float = 0.0) -> str:
    """Outline `value` with its baseline at `y`. Characters the font lacks render as '?'."""
    _, glyphs, _, upem = _font(family, weight)
    scale = size / upem
    parts = []
    for char in value:
        name = _glyph_name(family, weight, char)
        d = _outline(family, weight, name)
        if d:
            parts.append(f'<path d="{d}" transform="translate({x:.2f} {y:.2f}) '
                         f'scale({scale:.5f} {-scale:.5f})"/>')
        x += glyphs[name].width * scale + tracking
    return f'<g fill="{color}" aria-label="{escape(value)}">{"".join(parts)}</g>'


def rect(x, y, w, h, fill: str, r: float = 0, stroke: str | None = None,
         stroke_width: float = 1, extra: str = '') -> str:
    s = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{s}{extra}/>'


def circle(cx, cy, r, fill: str) -> str:
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'


@lru_cache(maxsize=None)
def _icon_source(name: str) -> tuple[tuple[float, ...], tuple[str, ...]]:
    path = ICONS / f'{name}.svg'
    if not path.exists():
        raise FileNotFoundError(f'icon not vendored: {name} (expected {path})')
    root = ET.parse(path).getroot()
    view_box = tuple(float(v) for v in root.get('viewBox').split())
    paths = tuple(el.get('d') for el in root.iter() if el.tag.endswith('path') and el.get('d'))
    return view_box, paths


def icon(name: str, x: float, y: float, size: float, color: str) -> str:
    """Inline a vendored single-colour icon into a size×size box with its top-left at (x, y)."""
    (min_x, min_y, w, h), paths = _icon_source(name)
    scale = size / max(w, h)
    body = ''.join(f'<path d="{d}"/>' for d in paths)
    return (f'<g fill="{color}" transform="translate({x:.2f} {y:.2f}) scale({scale:.5f}) '
            f'translate({-min_x:g} {-min_y:g})">{body}</g>')


def document(height: int, title: str, body: str, css: str = '') -> str:
    style = f'<style>{css}</style>' if css else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
            f'viewBox="0 0 {WIDTH} {height}" role="img"><title>{escape(title)}</title>'
            f'{style}{body}</svg>')


def validate(svg: str) -> None:
    size = len(svg.encode('utf-8'))
    if size > MAX_BYTES:
        raise ValueError(f'SVG is {size} bytes; limit is {MAX_BYTES} bytes')
    title = ET.fromstring(svg).find(f'{SVG_NS}title')
    if title is None or not (title.text or '').strip():
        raise ValueError('SVG is missing a <title>')


def write(path: Path, svg: str) -> None:
    validate(svg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding='utf-8', newline='\n')

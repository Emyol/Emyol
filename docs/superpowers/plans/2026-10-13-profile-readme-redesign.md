# Terminal / Phosphor Profile README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static "Silver Field" GitHub profile README for `Emyol/Emyol` with a terminal-styled page (B1 Phosphor) that has animated SVGs, a neofetch-style stack panel, a stats panel and recent commits that refresh daily, and a contribution snake.

**Architecture:** Python scripts render every image as a standalone SVG, with text outlined to paths, in a dark and a light variant. `tools/svg.py` holds primitives, `tools/term.py` holds terminal-window components and motion CSS, `tools/build_static.py` renders the rarely-changing art (committed), and `tools/build_live.py` renders the stats panel and rewrites a marked README block. A daily GitHub Action runs `build_live.py` plus Platane/snk. The README embeds every image through `<picture>` so it follows GitHub's theme.

**Tech Stack:** Python 3.13, fontTools 4.60.1 (glyph outlining), stdlib `urllib` (GitHub GraphQL), pytest 8.3.5, Playwright 1.49.1 (previews only), GitHub Actions (`actions/checkout@v7`, `actions/setup-python@v7`, `Platane/snk@v3`, `crazy-max/ghaction-github-pages@v5`).

**Spec:** `docs/superpowers/specs/2026-10-13-profile-readme-redesign-design.md`

**Working directory for every command:** `C:/Users/Miel/orca/workspaces/githut-profile-readme/polyp` (Git Bash). Branch: `Emyol/create-github-profile-readme`.

## Global Constraints

- Canvas width is 1200 units for every SVG. Terminal/body text ≥ 26 units, secondary text ≥ 22 units (`SIZE_BODY = 28`, `SIZE_SECONDARY = 24`, `SIZE_SMALL = 22`).
- Every SVG: parses as XML, has a non-empty `<title>`, ≤ 300,000 bytes, all text outlined to `<path>` with `aria-label`.
- Dark palette: bg `#0c100e`, chrome `#151b17`, fg `#d7e4da`, dim `#7d8f82`, prompt `#7ee2a0`, string `#a8d8ff`, line `#223028`, heat `#141a16 #1d3a28 #2b6a44 #4fa36e #7ee2a0`.
- Light palette: bg `#f4f7f4`, chrome `#e8eee9`, fg `#1d2a21`, dim `#5d6e62`, prompt `#1f7a43`, string `#0b5cad`, line `#cfdcd2`, heat `#e3e9e4 #b9dcc4 #7cc296 #3f9a62 #1f7a43`.
- Fonts: Geist (sans, name and project titles) and Geist Mono (all terminal text), both OFL, both variable `wght` 100–900.
- Motion: entrances use `cubic-bezier(.23,1,.32,1)`, 420 ms, `translateY(6px)` + opacity. Typing uses 50 ms per character (minimum 300 ms) with `steps(n)`. Stagger is 60 ms. Every intro finishes ≤ 3.2 s. Only `transform` and `opacity` animate. The only infinite animations are the hero cursor (`1.06s steps(1) infinite`) and the snake. `@media (prefers-reduced-motion:reduce)` disables everything. The un-animated state is always the complete final frame.
- No hover affordances (no ↗ arrows, no button styling).
- Every README image uses `<picture>` with a `(prefers-color-scheme: dark)` source and a light `<img>` fallback with non-empty `alt`.
- Links: Portfolio `https://project-miel.vercel.app`, LinkedIn `https://www.linkedin.com/in/amiel-acu%C3%B1a`, Email `mailto:acunaamieljosiah@gmail.com`.
- Icons: Simple Icons `16.30.0` (CC0-1.0); Playwright from Devicon `v2.16.0` `playwright-plain.svg` (MIT). No Framer Motion icon.
- GitHub login `Emyol`. The profile repo `Emyol/Emyol` is excluded from recent commits. Manila is fixed UTC+8 (no DST, no tzdata dependency). Cron `0 16 * * *`.
- Never show followers or stars. No third-party stats services.
- Never commit stats generated from the test fixture. Live assets in the repo must come from real API data.
- Runtime dependency is only `fonttools==4.60.1`. HTTP uses stdlib `urllib`.
- Every commit message ends with a `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` trailer.
- Pushing to GitHub is outward-facing: get the user's explicit confirmation immediately before the push in Task 10.

## Review Focus

1. **Commit messages containing Markdown/HTML (`<script>`, `*bold*`, backticks, `[link]`) or longer than 72 characters.** These must render as literal, escaped text truncated to 72 characters with `…`, never as live markup. Tested in Task 5 (`test_recent_lines_escape_markup`, `test_recent_lines_truncate_long_messages`).
2. **No qualifying recent commits** (all merges, all by bots, or no recent pushes). The README block must show `- _No recent public commits._`, not be empty, and the run must not crash. Tested in Task 5 (`test_recent_lines_when_nothing_qualifies`).
3. **A quiet account:** zero contributions today and yesterday, and repos with no language data. The panel must show `0 days` and `no language data yet`, and still be a valid SVG. Tested in Task 5 (`test_streak_zero_when_today_and_yesterday_empty`) and Task 6 (`test_panel_without_languages_is_valid`).
4. **GitHub returns HTTP 200 with an `errors` array** (rate limit, schema change), a null user, a network failure, or a malformed payload. Exit code 1, and *no* file (SVG or README) is touched. Tested in Task 6 (`test_graphql_errors_raise`, `test_http_failure_raises`, `test_null_user_raises`, `test_malformed_payload_writes_nothing`).
5. **Text with XML-special characters (`C++ & <F#>`) or characters the fonts lack (CJK, emoji).** Labels must be escaped, missing glyphs fall back to `?`, and the SVG must still parse. Tested in Task 1 (`test_text_escapes_label_and_parses`, `test_unknown_glyph_falls_back_to_question_mark`).

---

## File Map

| File | Responsibility |
|---|---|
| `tools/svg.py` | Palettes, fonts, text→path, text width, glyph coverage, shapes, icon inlining, document wrapper, validation |
| `tools/term.py` | Terminal window frame, prompt lines, typing cover, rise groups, cursor, icon+label flow layout, motion CSS, size constants |
| `tools/build_static.py` | Content constants (projects, stack, copy) and builders for hero, prompt bars, work strips, stack panel. Writes `assets/static/` |
| `tools/stats.py` | Pure logic: streaks, language share, recent-commit filtering, Markdown escaping, README block replacement |
| `tools/github_api.py` | One GraphQL query + error handling |
| `tools/build_live.py` | Glue: fetch/fixture → summarize → stats panel SVGs + README block, written only if all succeed |
| `tools/preview.py` | Playwright contact sheets (dark/light × 830/360 px) into `previews/` (git-ignored) |
| `tools/icons/*.svg`, `tools/icons/ICONS-LICENSE.md` | Vendored brand icons + licence notes |
| `tools/fonts/GeistMono[wght].ttf` | New vendored font (OFL already in `tools/fonts/OFL.txt`) |
| `tools/requirements.txt`, `tools/requirements-dev.txt` | Pinned deps |
| `tools/tests/` | `conftest.py`, one test file per module, `fixtures/user.json` |
| `README.md` | Hand-authored layout with `<picture>` tags and `recent` markers |
| `.github/workflows/profile.yml` | Daily snake + live refresh |
| *(deleted)* `tools/build_visuals.py`, `assets/{silver-field,kitako,icare,bekilang,citysense,toolkit}.svg` | Old Silver Field art |

---

### Task 1: Base the branch on GitHub's history and build the SVG primitives

**Files:**
- Create: `tools/svg.py`, `tools/requirements.txt`, `tools/requirements-dev.txt`, `tools/tests/conftest.py`, `tools/tests/test_svg.py`, `tools/fonts/GeistMono[wght].ttf`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nothing.
- Produces (`tools/svg.py`):
  - constants `TOOLS: Path`, `ROOT: Path`, `ICONS: Path`, `WIDTH = 1200`, `MAX_BYTES = 300_000`, `THEMES = ('dark', 'light')`, `EASE_OUT = 'cubic-bezier(.23,1,.32,1)'`, `PALETTES: dict[str, dict]` (keys `bg chrome fg dim prompt string line heat`; `heat` is a 5-tuple)
  - `text(value: str, x: float, y: float, size: float, color: str, family: str = 'mono', weight: int = 400, tracking: float = 0.0) -> str`, where `y` is the baseline
  - `text_width(value: str, size: float, family: str = 'mono', weight: int = 400, tracking: float = 0.0) -> float`
  - `missing_glyphs(value: str, family: str = 'mono', weight: int = 400) -> set[str]`
  - `rect(x, y, w, h, fill: str, r: float = 0, stroke: str | None = None, stroke_width: float = 1, extra: str = '') -> str`
  - `circle(cx, cy, r, fill: str) -> str`
  - `document(height: int, title: str, body: str, css: str = '') -> str`
  - `validate(svg: str) -> None` (raises `ValueError` or `xml.etree.ElementTree.ParseError`)
  - `write(path: Path, svg: str) -> None`

- [ ] **Step 1: Connect the GitHub remote and check the untracked files match it**

```bash
git remote get-url origin 2>/dev/null || git remote add origin https://github.com/Emyol/Emyol.git
git fetch origin main
for f in README.md .gitignore tools/build_visuals.py tools/fonts/OFL.txt "tools/fonts/Geist[wght].ttf" assets/*.svg; do
  if git cat-file -e "origin/main:$f" 2>/dev/null; then
    git show "origin/main:$f" | tr -d '\r' | cmp -s - <(tr -d '\r' < "$f") && echo "same  $f" || echo "DIFF  $f"
  else echo "LOCAL-ONLY $f"; fi
done
```

Expected: every line says `same`, except `.gitignore`, which is `DIFF` because the spec commit added `.superpowers/`. **If any other file says `DIFF`, stop and show the user the diff.** Those are unpublished local edits and must not be lost.

- [ ] **Step 2: Move the untracked copies aside and rebase onto `origin/main`**

```bash
B="$HOME/profile-readme-backup-2026-10-13"; mkdir -p "$B"
mv README.md assets tools "$B"/
git rebase --onto origin/main d866952
git log --oneline -3
ls README.md assets tools/build_visuals.py
```

Expected: the log shows the spec commit on top of GitHub's history, and the files are present again, tracked. If the rebase conflicts on `.gitignore`, keep both sides' lines (`previews/`, `__pycache__/`, `.superpowers/`) and run `git rebase --continue`. Tell the user the backup folder path so they can delete it later.

- [ ] **Step 3: Vendor Geist Mono, pin dependencies, ignore caches**

```bash
curl -fsSL -o "tools/fonts/GeistMono[wght].ttf" "https://github.com/google/fonts/raw/main/ofl/geistmono/GeistMono%5Bwght%5D.ttf"
printf 'fonttools==4.60.1\n' > tools/requirements.txt
printf -- '-r requirements.txt\npytest==8.3.5\nplaywright==1.49.1\n' > tools/requirements-dev.txt
grep -qx '.pytest_cache/' .gitignore || printf '.pytest_cache/\n' >> .gitignore
python -m pip install -r tools/requirements-dev.txt
```

Geist Mono is covered by the existing `tools/fonts/OFL.txt` (same foundry, same licence).

- [ ] **Step 4: Write `tools/tests/conftest.py` and the failing tests**

`tools/tests/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

`tools/tests/test_svg.py`:

```python
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
    assert missing_glyphs('a\u4e00b') == {'\u4e00'}
    assert text_width('a\u4e00b', 26) == pytest.approx(text_width('a?b', 26))
    text('a\u4e00b', 0, 0, 26, '#fff')  # must not raise


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
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `python -m pytest tools/tests/test_svg.py -q`
Expected: collection error `ModuleNotFoundError: No module named 'svg'`.

- [ ] **Step 6: Implement `tools/svg.py`**

```python
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
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python -m pytest tools/tests/test_svg.py -q`
Expected: `9 passed`.

- [ ] **Step 8: Commit**

```bash
git add .gitignore tools/svg.py tools/requirements.txt tools/requirements-dev.txt tools/tests/conftest.py tools/tests/test_svg.py "tools/fonts/GeistMono[wght].ttf"
git commit -m "feat: add SVG primitives with outlined Geist and Geist Mono text" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Vendor brand icons and inline them

**Files:**
- Create: `tools/icons/*.svg` (24 files), `tools/icons/ICONS-LICENSE.md`, `tools/tests/test_icons.py`
- Modify: `tools/svg.py` (add `icon`)

**Interfaces:**
- Consumes: `ICONS` from `svg.py`.
- Produces: `icon(name: str, x: float, y: float, size: float, color: str) -> str` in `svg.py`. `(x, y)` is the top-left corner, `size` is the edge of the square box, and it raises `FileNotFoundError` naming the icon if it isn't vendored.

- [ ] **Step 1: Download the icons**

```bash
mkdir -p tools/icons
V=16.30.0
for s in typescript javascript python dart cplusplus nextdotjs react tailwindcss shadcnui gsap flutter onnx supabase prisma flask pandas scikitlearn vitest git vercel figma leaflet vite; do
  curl -fsSL "https://cdn.jsdelivr.net/npm/simple-icons@$V/icons/$s.svg" -o "tools/icons/$s.svg"
done
curl -fsSL "https://cdn.jsdelivr.net/gh/devicons/devicon@v2.16.0/icons/playwright/playwright-plain.svg" -o tools/icons/playwright.svg
ls tools/icons | wc -l
```

Expected: `24`.

- [ ] **Step 2: Write `tools/icons/ICONS-LICENSE.md`**

```markdown
# Icon sources

- All icons except `playwright.svg`: [Simple Icons](https://simpleicons.org) v16.30.0, CC0-1.0.
- `playwright.svg`: [Devicon](https://devicon.dev) v2.16.0 `playwright-plain.svg`, MIT.

Brand names and logos are trademarks of their owners. They are used here only to name the technologies used in these projects.
```

- [ ] **Step 3: Write the failing tests**

`tools/tests/test_icons.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `python -m pytest tools/tests/test_icons.py -q`
Expected: `ImportError: cannot import name 'icon' from 'svg'`.

- [ ] **Step 5: Add `icon` to `tools/svg.py`** (append below `circle`)

```python
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
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest tools/tests -q`
Expected: `14 passed`.

- [ ] **Step 7: Commit**

```bash
git add tools/icons tools/svg.py tools/tests/test_icons.py
git commit -m "feat: vendor stack icons and inline them as tinted paths" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Terminal components and motion CSS

**Files:**
- Create: `tools/term.py`, `tools/tests/test_term.py`

**Interfaces:**
- Consumes: `EASE_OUT, WIDTH, circle, icon, rect, text, text_width` from `svg.py`.
- Produces (`tools/term.py`):
  - constants `CHROME_H = 52`, `SIZE_BODY = 28`, `SIZE_SECONDARY = 24`, `SIZE_SMALL = 22`, `MS_PER_CHAR = 50`, `MOTION_CSS: str`
  - `window(height: int, title: str | None, body: str, p: dict) -> str`: rounded clip, background, optional title bar with 3 dots, and a border. `p` is one `PALETTES[theme]` dict.
  - `rise(content: str, delay_ms: int) -> str`
  - `typed(content: str, x: float, y_top: float, width: float, height: float, bg: str, delay_ms: int, chars: int) -> str`
  - `prompt_line(command: str, x: float, y: float, p: dict, delay_ms: int | None = None, size: float = SIZE_BODY) -> str`: `$ command`, typed if `delay_ms` is given
  - `cursor(x: float, y_top: float, w: float, h: float, color: str) -> str`
  - `flow(items: list[tuple[str, str]], x0: float, x_max: float, y: float, p: dict, size: float = SIZE_SMALL, icon_size: float = 28, line_h: float = 44, gap: float = 26) -> tuple[str, int]`: lays out `(icon_name, label)` pairs and returns `(svg, rows_used)`

- [ ] **Step 1: Write the failing tests**

`tools/tests/test_term.py`:

```python
from svg import PALETTES
from term import (MOTION_CSS, SIZE_BODY, SIZE_SECONDARY, SIZE_SMALL, cursor, flow,
                  prompt_line, rise, typed, window)

P = PALETTES['dark']


def test_sizes_respect_legibility_floor():
    assert SIZE_BODY >= 26 and SIZE_SECONDARY >= 22 and SIZE_SMALL >= 22


def test_window_draws_title_bar_clip_and_border():
    out = window(200, 'neofetch', '', P)
    assert 'aria-label="neofetch"' in out
    assert f'fill="{P["chrome"]}"' in out
    assert 'clip-path="url(#win)"' in out
    assert f'stroke="{P["line"]}"' in out


def test_window_without_title_has_no_title_bar():
    assert f'fill="{P["chrome"]}"' not in window(84, None, '', P)


def test_rise_group_carries_delay_and_no_transform_attribute():
    out = rise('<rect/>', 360)
    assert out.startswith('<g class="rise" style="animation-delay:360ms">')
    assert 'transform=' not in out.split('>', 1)[0]


def test_typed_cover_steps_once_per_character():
    out = typed('', 10, 20, 100, 30, '#000', 200, 6)
    assert 'class="type"' in out
    assert 'animation-timing-function:steps(6)' in out
    assert 'animation-duration:300ms' in out
    assert 'animation-delay:200ms' in out


def test_typed_duration_is_50ms_per_character():
    assert 'animation-duration:600ms' in typed('', 0, 0, 1, 1, '#000', 0, 12)


def test_prompt_line_is_static_without_delay():
    out = prompt_line('exit', 40, 54, P)
    assert 'class="type"' not in out
    assert 'aria-label="exit"' in out and 'aria-label="$ "' in out


def test_prompt_line_types_with_delay():
    assert 'class="type"' in prompt_line('whoami', 40, 54, P, delay_ms=200)


def test_cursor_is_the_blinking_rect():
    assert 'class="cursor"' in cursor(80, 350, 16, 28, P['prompt'])


def test_motion_css_rules():
    assert 'cubic-bezier(.23,1,.32,1)' in MOTION_CSS
    assert 'translateY(6px)' in MOTION_CSS
    assert '1.06s steps(1) infinite' in MOTION_CSS
    assert MOTION_CSS.count('infinite') == 1
    assert '@media (prefers-reduced-motion:reduce)' in MOTION_CSS


def test_flow_wraps_when_out_of_room():
    items = [('react', 'React'), ('vite', 'Vite'), ('git', 'Git')]
    assert flow(items, 0, 10_000, 100, P)[1] == 1
    assert flow(items, 0, 150, 100, P)[1] == 3


def test_flow_draws_icon_and_label():
    out, _ = flow([('react', 'React')], 0, 1000, 100, P)
    assert 'aria-label="React"' in out
    assert f'fill="{P["prompt"]}"' in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/tests/test_term.py -q`
Expected: `ModuleNotFoundError: No module named 'term'`.

- [ ] **Step 3: Implement `tools/term.py`**

```python
"""Terminal-window building blocks and the shared motion CSS.

Motion plays once and settles. The un-animated state of every element is its
final frame, so reduced-motion viewers and static renderers see complete content.
Never put a `class="rise"` / `class="type"` element on a node that also has a
`transform=` attribute: CSS transforms replace attribute transforms.
"""
from __future__ import annotations

from svg import EASE_OUT, WIDTH, circle, icon, rect, text, text_width

CHROME_H = 52
SIZE_BODY = 28
SIZE_SECONDARY = 24
SIZE_SMALL = 22
MS_PER_CHAR = 50

MOTION_CSS = (
    f'.rise{{animation:rise 420ms {EASE_OUT} both}}'
    '.type{transform-box:fill-box;transform-origin:right;transform:scaleX(0);'
    'animation-name:type;animation-fill-mode:both}'
    '.cursor{animation:blink 1.06s steps(1) infinite}'
    '@keyframes rise{from{opacity:0;transform:translateY(6px)}}'
    '@keyframes type{from{transform:scaleX(1)}}'
    '@keyframes blink{50%{opacity:0}}'
    '@media (prefers-reduced-motion:reduce){.rise,.type,.cursor{animation:none}}'
)


def window(height: int, title: str | None, body: str, p: dict) -> str:
    out = (f'<defs><clipPath id="win"><rect width="{WIDTH}" height="{height}" rx="12"/>'
           f'</clipPath></defs><g clip-path="url(#win)">' + rect(0, 0, WIDTH, height, p['bg']))
    if title is not None:
        out += rect(0, 0, WIDTH, CHROME_H, p['chrome']) + rect(0, CHROME_H - 1, WIDTH, 1, p['line'])
        out += ''.join(circle(30 + i * 22, CHROME_H / 2, 7, p['line']) for i in range(3))
        out += text(title, 104, CHROME_H / 2 + 8, SIZE_SMALL, p['dim'])
    out += body + '</g>'
    return out + rect(0.5, 0.5, WIDTH - 1, height - 1, 'none', 12, p['line'], 1)


def rise(content: str, delay_ms: int) -> str:
    return f'<g class="rise" style="animation-delay:{delay_ms}ms">{content}</g>'


def typed(content: str, x: float, y_top: float, width: float, height: float, bg: str,
          delay_ms: int, chars: int) -> str:
    """Hide `content` behind a background-coloured cover that shrinks one character per step."""
    duration = max(300, chars * MS_PER_CHAR)
    cover = rect(round(x, 2), round(y_top, 2), round(width + 2, 2), round(height, 2), bg,
                 extra=(f' class="type" style="animation-delay:{delay_ms}ms;'
                        f'animation-duration:{duration}ms;animation-timing-function:steps({chars})"'))
    return content + cover


def prompt_line(command: str, x: float, y: float, p: dict, delay_ms: int | None = None,
                size: float = SIZE_BODY) -> str:
    prefix = text('$ ', x, y, size, p['prompt'])
    cx = x + text_width('$ ', size)
    line = text(command, cx, y, size, p['fg'])
    if delay_ms is None:
        return prefix + line
    return prefix + typed(line, cx, y - size, text_width(command, size), size * 1.35,
                          p['bg'], delay_ms, len(command))


def cursor(x: float, y_top: float, w: float, h: float, color: str) -> str:
    return rect(x, y_top, w, h, color, extra=' class="cursor"')


def flow(items: list[tuple[str, str]], x0: float, x_max: float, y: float, p: dict,
         size: float = SIZE_SMALL, icon_size: float = 28, line_h: float = 44,
         gap: float = 26) -> tuple[str, int]:
    out, x, rows = '', x0, 1
    for name, label in items:
        width = icon_size + 10 + text_width(label, size)
        if x > x0 and x + width > x_max:
            x, y, rows = x0, y + line_h, rows + 1
        out += icon(name, x, y - icon_size + 5, icon_size, p['prompt'])
        out += text(label, x + icon_size + 10, y, size, p['fg'])
        x += width + gap
    return out, rows
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tools/tests -q`
Expected: `26 passed`.

- [ ] **Step 5: Commit**

```bash
git add tools/term.py tools/tests/test_term.py
git commit -m "feat: add terminal window components and play-once motion CSS" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Static art: hero, prompt bars, work strips, neofetch stack

**Files:**
- Create: `tools/build_static.py`, `tools/tests/test_build_static.py`, `assets/static/*.svg` (18 generated files)

**Interfaces:**
- Consumes: `PALETTES, ROOT, THEMES, WIDTH, document, icon, rect, text, text_width, validate, write` from `svg.py`; `CHROME_H, MOTION_CSS, SIZE_BODY, SIZE_SECONDARY, SIZE_SMALL, cursor, flow, prompt_line, rise, window` from `term.py`.
- Produces (`tools/build_static.py`): constants `PROJECTS: list[dict]` (keys `slug name tagline icons`), `STACK: list[tuple[str, list[tuple[str, str]]]]`, `SUN: list[str]`, `ROLE: tuple[str, str, str]`, `BARS: dict[str, tuple[str, str, str]]` (`command, comment, title`). Functions `hero(theme) -> str`, `prompt_bar(command, comment, theme, title) -> str`, `work_strip(index, project, theme) -> str`, `stack_panel(theme) -> str`, `build_all() -> dict[str, str]` (filename → SVG), `all_copy() -> list[tuple[str, int, str]]` (`family, weight, string`), `main() -> None`.
- Output file names (used by README in Task 7): `hero-{t}.svg`, `work-header-{t}.svg`, `work-{kitako|icare|bekilang|citysense}-{t}.svg`, `stack-{t}.svg`, `graph-header-{t}.svg`, `footer-{t}.svg`, for `t` in `dark`, `light`.

- [ ] **Step 1: Write the failing tests**

`tools/tests/test_build_static.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/tests/test_build_static.py -q`
Expected: `ModuleNotFoundError: No module named 'build_static'`.

- [ ] **Step 3: Implement `tools/build_static.py`**

```python
"""Build the committed terminal artwork (hero, work strips, stack, prompt bars).

Run: python tools/build_static.py   → writes assets/static/*-{dark,light}.svg
"""
from __future__ import annotations

from svg import PALETTES, ROOT, THEMES, WIDTH, document, icon, rect, text, text_width, validate, write
from term import (CHROME_H, MOTION_CSS, SIZE_BODY, SIZE_SECONDARY, SIZE_SMALL, cursor, flow,
                  prompt_line, rise, window)

STATIC = ROOT / 'assets' / 'static'

ROLE = ('Student leader · web & mobile · ', 'FEU Tech', ', Manila')

PROJECTS = [
    {'slug': 'kitako', 'name': 'KitaKo', 'tagline': 'find a photo in your own words',
     'icons': ['flutter', 'dart', 'onnx']},
    {'slug': 'icare', 'name': 'iCARE Reservation', 'tagline': 'room bookings for 700+ STEM students',
     'icons': ['nextdotjs', 'react', 'javascript']},
    {'slug': 'bekilang', 'name': 'BekiLang', 'tagline': 'Swardspeak, compiled',
     'icons': ['python', 'flask']},
    {'slug': 'citysense', 'name': 'CitySense', 'tagline': 'urban heat & greenspace from orbit',
     'icons': ['typescript', 'react', 'leaflet', 'vite']},
]

STACK = [
    ('Languages', [('typescript', 'TypeScript'), ('javascript', 'JavaScript'), ('python', 'Python'),
                   ('dart', 'Dart'), ('cplusplus', 'C++')]),
    ('Web', [('nextdotjs', 'Next.js'), ('react', 'React'), ('tailwindcss', 'Tailwind CSS'),
             ('shadcnui', 'shadcn/ui'), ('gsap', 'GSAP')]),
    ('Mobile', [('flutter', 'Flutter'), ('onnx', 'ONNX Runtime')]),
    ('Data', [('supabase', 'Supabase'), ('prisma', 'Prisma'), ('flask', 'Flask'),
              ('pandas', 'pandas'), ('scikitlearn', 'scikit-learn')]),
    ('Testing', [('playwright', 'Playwright'), ('vitest', 'Vitest')]),
    ('Tools', [('git', 'Git'), ('vercel', 'Vercel'), ('figma', 'Figma'), ('leaflet', 'Leaflet')]),
]

# A small sun for the Philippine flag.
SUN = [
    r'    \   |   /',
    r"  '-. ;;; .-'",
    r' -==;;;;;;;==-',
    r"  .-' ;;; '-.",
    r'    /   |   \ ',
]

BARS = {
    'work-header': ('ls ~/work', '--pinned', '$ ls ~/work --pinned: pinned projects'),
    'graph-header': ('git log --graph --all', '', '$ git log --graph --all: contribution graph'),
    'footer': ('exit', '— salamat sa pagbisita · thanks for stopping by',
               '$ exit: salamat sa pagbisita, thanks for stopping by'),
}

HERO_TITLE = 'Amiel Acuña: student leader building web and mobile software at FEU Tech, Manila.'


def hero(theme: str) -> str:
    p = PALETTES[theme]
    body = prompt_line('whoami', 48, 118, p, delay_ms=200)
    name = text('Amiel Acuña', 48, 212, 84, p['fg'], 'sans', 800, -2)
    name += text('.', 48 + text_width('Amiel Acuña', 84, 'sans', 800, -2), 212, 84,
                 p['prompt'], 'sans', 800)
    body += rise(name, 650)
    body += prompt_line('cat role.txt', 48, 274, p, delay_ms=1050)
    x, role = 48, ''
    for part, color in zip(ROLE, (p['fg'], p['string'], p['fg'])):
        role += text(part, x, 322, SIZE_BODY, color)
        x += text_width(part, SIZE_BODY)
    body += rise(role, 1800)
    caret_x = 48 + text_width('$ ', SIZE_BODY)
    body += rise(text('$ ', 48, 372, SIZE_BODY, p['prompt'])
                 + cursor(caret_x, 349, 16, 28, p['prompt']), 2100)
    return document(400, HERO_TITLE, window(400, 'miel@manila: ~', body, p), MOTION_CSS)


def prompt_bar(command: str, comment: str, theme: str, title: str) -> str:
    p = PALETTES[theme]
    body = prompt_line(command, 40, 54, p)
    if comment:
        body += text(comment, 40 + text_width(f'$ {command}  ', SIZE_BODY), 54, SIZE_SECONDARY, p['dim'])
    return document(84, title, window(84, None, body, p))


def work_strip(index: int, project: dict, theme: str) -> str:
    p = PALETTES[theme]
    body = text(f'{index + 1:02d}', 40, 86, SIZE_BODY, p['dim'])
    body += text(project['name'], 120, 70, 40, p['fg'], 'sans', 700)
    body += text(project['tagline'], 120, 112, SIZE_SECONDARY, p['dim'])
    icons = project['icons']
    x = WIDTH - 40 - len(icons) * 40 - (len(icons) - 1) * 16
    for name in icons:
        body += icon(name, x, 55, 40, p['prompt'])
        x += 56
    title = f"{index + 1:02d} {project['name']}: {project['tagline']}"
    return document(150, title, window(150, None, rise(body, 120 + index * 60), p), MOTION_CSS)


def stack_panel(theme: str) -> str:
    p = PALETTES[theme]
    top = CHROME_H + 62
    sun = ''.join(text(line, 48, top + i * 30, SIZE_SECONDARY, p['prompt']) for i, line in enumerate(SUN))
    sun += text('miel@manila', 48, top + len(SUN) * 30 + 30, SIZE_SMALL, p['dim'])
    body = rise(sun, 100)  # the title bar already reads "neofetch"
    y = top
    for i, (key, items) in enumerate(STACK):
        row = text(key, 300, y, SIZE_SECONDARY, p['prompt'], weight=700)
        items_svg, rows = flow(items, 460, WIDTH - 40, y, p)
        body += rise(row + items_svg, 150 + i * 60)
        y += rows * 44 + 14
    swatches = ''.join(rect(300 + i * 34, y, 26, 14, color, 3)
                       for i, color in enumerate([*p['heat'], p['string']]))
    body += rise(swatches, 150 + len(STACK) * 60)
    height = int(max(y + 50, top + (len(SUN) + 1) * 30 + 40))
    title = 'neofetch: ' + '; '.join(f"{key}: {', '.join(label for _, label in items)}"
                                     for key, items in STACK)
    return document(height, title, window(height, 'neofetch', body, p), MOTION_CSS)


def build_all() -> dict[str, str]:
    files = {}
    for theme in THEMES:
        files[f'hero-{theme}.svg'] = hero(theme)
        for stem, (command, comment, title) in BARS.items():
            files[f'{stem}-{theme}.svg'] = prompt_bar(command, comment, theme, title)
        for index, project in enumerate(PROJECTS):
            files[f"work-{project['slug']}-{theme}.svg"] = work_strip(index, project, theme)
        files[f'stack-{theme}.svg'] = stack_panel(theme)
    return files


def all_copy() -> list[tuple[str, int, str]]:
    copy = [('sans', 800, 'Amiel Acuña.'), ('mono', 400, '$ whoami'), ('mono', 400, '$ cat role.txt'),
            ('mono', 400, ''.join(ROLE)), ('mono', 400, 'miel@manila: ~'), ('mono', 400, 'neofetch'),
            ('mono', 400, 'miel@manila'), ('mono', 400, '0123456789')]
    copy += [('sans', 700, p['name']) for p in PROJECTS]
    copy += [('mono', 400, p['tagline']) for p in PROJECTS]
    copy += [('mono', 700, key) for key, _ in STACK]
    copy += [('mono', 400, label) for _, items in STACK for _, label in items]
    copy += [('mono', 400, line) for line in SUN]
    copy += [('mono', 400, f'$ {command} {comment}') for command, comment, _ in BARS.values()]
    return copy


def main() -> None:
    files = build_all()
    for svg in files.values():
        validate(svg)
    for name, svg in files.items():
        write(STATIC / name, svg)
    print(f'Built {len(files)} static SVGs into {STATIC.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tools/tests -q`
Expected: `35 passed`.

- [ ] **Step 5: Build the assets and check sizes**

```bash
python tools/build_static.py
ls -l assets/static | awk '{print $5, $9}' | sort -n | tail -3
```

Expected: `Built 18 static SVGs into assets/static`. The largest file is under 300000 bytes (`validate` would have raised otherwise).

- [ ] **Step 6: Commit**

```bash
git add tools/build_static.py tools/tests/test_build_static.py assets/static
git commit -m "feat: build terminal hero, work strips, neofetch stack and prompt bars" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Live-data logic (streaks, language share, recent commits, README block)

**Files:**
- Create: `tools/stats.py`, `tools/tests/test_stats.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (pure stdlib).
- Produces (`tools/stats.py`):
  - `MANILA = timezone(timedelta(hours=8))`, `START = '<!-- recent:start -->'`, `END = '<!-- recent:end -->'`, `MAX_MESSAGE = 72`
  - `@dataclass(frozen=True) StatsView(year: int, contributions_this_year: int, current_streak: int, longest_streak: int, public_repos: int, languages: tuple[tuple[str, int], ...])`
  - `@dataclass(frozen=True) Commit(sha7: str, repo: str, message: str, url: str, when: str)`
  - `streaks(days: Iterable[tuple[date, int]], today: date) -> tuple[int, int]` returns `(current, longest)`
  - `language_share(repos: Iterable[dict], top: int = 5) -> tuple[tuple[str, int], ...]`: percentages sum to 100, with `Other` last
  - `recent_commits(repos: Iterable[dict], login: str, exclude: str, limit: int = 3) -> list[Commit]`
  - `escape_markdown(value: str) -> str`, `shorten(value: str, limit: int = MAX_MESSAGE) -> str`
  - `recent_lines(commits: list[Commit]) -> list[str]`
  - `replace_block(readme: str, lines: list[str]) -> str`

- [ ] **Step 1: Write the failing tests**

`tools/tests/test_stats.py`:

```python
from datetime import date, timedelta

import pytest

from stats import (END, START, Commit, escape_markdown, language_share, recent_commits,
                   recent_lines, replace_block, shorten, streaks)

TODAY = date(2026, 10, 13)


def run(counts, end=TODAY):
    """counts[-1] is `end`, counts[-2] the day before, and so on."""
    return [(end - timedelta(days=len(counts) - 1 - i), c) for i, c in enumerate(counts)]


def test_streak_counts_consecutive_days_ending_today():
    assert streaks(run([0, 2, 1, 4]), TODAY) == (3, 3)


def test_streak_survives_an_empty_today():
    assert streaks(run([1, 1, 0]), TODAY) == (2, 2)


def test_streak_zero_when_today_and_yesterday_empty():
    assert streaks(run([5, 0, 0]), TODAY) == (0, 1)


def test_longest_streak_spans_gaps_correctly():
    assert streaks(run([1, 1, 1, 1, 0, 1]), TODAY) == (1, 4)


def test_streak_crosses_the_year_boundary():
    jan1 = date(2027, 1, 1)
    assert streaks(run([1, 1, 1], end=jan1), jan1) == (3, 3)


def test_streak_of_nothing():
    assert streaks([], TODAY) == (0, 0)


def lang_repo(*pairs, fork=False):
    return {'isFork': fork, 'languages': {'edges': [{'size': s, 'node': {'name': n}} for n, s in pairs]}}


def test_language_share_sums_to_100_with_equal_thirds():
    assert language_share([lang_repo(('A', 1), ('B', 1), ('C', 1))]) == (('A', 34), ('B', 33), ('C', 33))


def test_language_share_excludes_forks_and_buckets_other():
    repos = [lang_repo(('TypeScript', 6000), ('CSS', 500)), lang_repo(('Python', 3000)),
             lang_repo(('Dart', 1500)), lang_repo(('JavaScript', 1000), ('HTML', 400)),
             lang_repo(('C++', 300)), lang_repo(('Rust', 99999), fork=True)]
    assert language_share(repos) == (('TypeScript', 47), ('Python', 24), ('Dart', 12),
                                     ('JavaScript', 8), ('CSS', 4), ('Other', 5))


def test_language_share_empty():
    assert language_share([lang_repo()]) == ()


def commit(oid, msg, when, login='Emyol'):
    return {'oid': oid, 'messageHeadline': msg, 'committedDate': when, 'url': f'https://x/{oid}',
            'author': {'user': {'login': login} if login else None}}


def repo(name, *commits, owner='Emyol'):
    ref = {'target': {'history': {'nodes': list(commits)}}} if commits else None
    return {'name': name, 'nameWithOwner': f'{owner}/{name}', 'defaultBranchRef': ref}


def test_recent_commits_filters_and_sorts():
    repos = [
        repo('pane', commit('a' * 40, 'add grid', '2026-10-12T10:00:00Z'),
             commit('b' * 40, 'Merge branch main', '2026-10-12T11:00:00Z')),
        repo('Emyol', commit('c' * 40, 'chore: refresh', '2026-10-13T00:00:00Z')),
        repo('site', commit('d' * 40, 'polish', '2026-10-11T09:00:00Z'),
             commit('e' * 40, 'deps: bump', '2026-10-12T12:00:00Z', login='dependabot[bot]'),
             commit('f' * 40, 'bot commit', '2026-10-12T13:00:00Z', login=None)),
        repo('empty'),
        repo('old', commit('9' * 40, 'older', '2026-09-01T00:00:00Z')),
    ]
    got = recent_commits(repos, 'Emyol', 'Emyol/Emyol')
    assert [(c.sha7, c.repo) for c in got] == [('aaaaaaa', 'pane'), ('ddddddd', 'site'), ('9999999', 'old')]


def test_recent_lines_escape_markup():
    line = recent_lines([Commit('abc1234', 'my_repo', 'hero <script> & *bold* `x` [y](z)', 'https://u', '')])[0]
    assert line == ('- [`abc1234`](https://u) **my\\_repo**: hero &lt;script&gt; &amp; '
                    '\\*bold\\* \\`x\\` \\[y\\]\\(z\\)')


def test_recent_lines_truncate_long_messages():
    assert shorten('x' * 100) == 'x' * 71 + '…'
    assert shorten('short') == 'short'
    line = recent_lines([Commit('abc1234', 'r', 'y' * 100, 'https://u', '')])[0]
    assert line.endswith('y' * 71 + '…')


def test_recent_lines_when_nothing_qualifies():
    assert recent_lines([]) == ['- _No recent public commits._']


def test_escape_markdown_leaves_plain_text_alone():
    assert escape_markdown('pane: add grid persistence') == 'pane: add grid persistence'


README = f'# hi\n\n{START}\nold line\n{END}\n\nbye\n'


def test_replace_block_swaps_only_between_markers():
    assert replace_block(README, ['- new']) == f'# hi\n\n{START}\n- new\n{END}\n\nbye\n'


def test_replace_block_is_idempotent():
    once = replace_block(README, ['- a', '- b'])
    assert replace_block(once, ['- a', '- b']) == once


@pytest.mark.parametrize('bad', ['# nothing', f'{START}\n{START}\n{END}', f'{END}\n{START}'])
def test_replace_block_rejects_missing_duplicate_or_reversed_markers(bad):
    with pytest.raises(ValueError):
        replace_block(bad, ['- x'])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/tests/test_stats.py -q`
Expected: `ModuleNotFoundError: No module named 'stats'`.

- [ ] **Step 3: Implement `tools/stats.py`**

```python
"""Pure logic behind the daily live section: streaks, language share, recent commits."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta, timezone
from typing import Iterable

MANILA = timezone(timedelta(hours=8))
START = '<!-- recent:start -->'
END = '<!-- recent:end -->'
MAX_MESSAGE = 72
_MD_SPECIAL = set('\\`*_[]()#|~!')


@dataclass(frozen=True)
class StatsView:
    year: int
    contributions_this_year: int
    current_streak: int
    longest_streak: int
    public_repos: int
    languages: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Commit:
    sha7: str
    repo: str
    message: str
    url: str
    when: str


def streaks(days: Iterable[tuple[date, int]], today: date) -> tuple[int, int]:
    """(current, longest). An empty today does not break a streak that ran through yesterday."""
    active = {day for day, count in days if count > 0}
    longest = run = 0
    previous = None
    for day in sorted(active):
        run = run + 1 if previous == day - timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    cursor = today if today in active else today - timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def language_share(repos: Iterable[dict], top: int = 5) -> tuple[tuple[str, int], ...]:
    """Top languages by bytes across non-fork repos, as whole percentages summing to 100."""
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get('isFork'):
            continue
        for edge in repo['languages']['edges']:
            name = edge['node']['name']
            totals[name] = totals.get(name, 0) + edge['size']
    grand = sum(totals.values())
    if not grand:
        return ()
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    buckets = ranked[:top]
    rest = sum(size for _, size in ranked[top:])
    if rest:
        buckets.append(('Other', rest))
    exact = [size * 100 / grand for _, size in buckets]
    percents = [int(v) for v in exact]
    order = sorted(range(len(exact)), key=lambda i: exact[i] - percents[i], reverse=True)
    for i in order[:100 - sum(percents)]:
        percents[i] += 1
    return tuple((name, pct) for (name, _), pct in zip(buckets, percents) if pct > 0)


def recent_commits(repos: Iterable[dict], login: str, exclude: str, limit: int = 3) -> list[Commit]:
    found = []
    for repo in repos:
        if repo['nameWithOwner'].lower() == exclude.lower() or not repo.get('defaultBranchRef'):
            continue
        for node in repo['defaultBranchRef']['target']['history']['nodes']:
            author = (node.get('author') or {}).get('user') or {}
            if author.get('login') != login or node['messageHeadline'].startswith('Merge'):
                continue
            found.append(Commit(node['oid'][:7], repo['name'], node['messageHeadline'],
                                node['url'], node['committedDate']))
    found.sort(key=lambda c: c.when, reverse=True)
    return found[:limit]


def escape_markdown(value: str) -> str:
    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return ''.join('\\' + ch if ch in _MD_SPECIAL else ch for ch in value)


def shorten(value: str, limit: int = MAX_MESSAGE) -> str:
    return value if len(value) <= limit else value[:limit - 1].rstrip() + '…'


def recent_lines(commits: list[Commit]) -> list[str]:
    if not commits:
        return ['- _No recent public commits._']
    return [f'- [`{c.sha7}`]({c.url}) **{escape_markdown(c.repo)}**: {escape_markdown(shorten(c.message))}'
            for c in commits]


def replace_block(readme: str, lines: list[str]) -> str:
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError('README needs exactly one recent:start and one recent:end marker')
    if readme.index(END) < readme.index(START):
        raise ValueError('recent:end comes before recent:start')
    head, rest = readme.split(START)
    tail = rest.split(END)[1]
    return f'{head}{START}\n' + '\n'.join(lines) + f'\n{END}{tail}'
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tools/tests -q`
Expected: `55 passed`.

- [ ] **Step 5: Commit**

```bash
git add tools/stats.py tools/tests/test_stats.py
git commit -m "feat: add streak, language share and recent-commit logic" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: GitHub fetch, stats panel and the all-or-nothing live build

**Files:**
- Create: `tools/github_api.py`, `tools/build_live.py`, `tools/tests/fixtures/user.json`, `tools/tests/test_build_live.py`

**Interfaces:**
- Consumes: everything listed in `stats.py` (Task 5); `PALETTES, ROOT, THEMES, WIDTH, document, rect, text, text_width, validate` from `svg.py`; `CHROME_H, MOTION_CSS, SIZE_BODY, SIZE_SECONDARY, SIZE_SMALL, prompt_line, rise, window` from `term.py`.
- Produces:
  - `github_api.py`: `class GitHubError(RuntimeError)`, `QUERY: str`, `fetch_profile(login: str, token: str, now: datetime, opener=urllib.request.urlopen) -> dict`, which returns GraphQL `data.user` with keys `thisYear`, `calendar`, `owned`, `recent`
  - `build_live.py`: `LOGIN = 'Emyol'`, `PROFILE_REPO = 'Emyol/Emyol'`, `summarize(user: dict, today: date) -> tuple[StatsView, list[Commit]]`, `stats_panel(view: StatsView, theme: str) -> str`, `render(user: dict, today: date, readme: str) -> tuple[dict[str, str], str]`, `main(argv: list[str] | None = None) -> int`. CLI flags `--fixture PATH`, `--readme PATH`, `--out DIR`, `--today YYYY-MM-DD`. Writes `stats-dark.svg` and `stats-light.svg`.

- [ ] **Step 1: Write the fixture `tools/tests/fixtures/user.json`**

This is test-only data. **Never run `build_live.py --fixture` against the real `README.md` or `assets/live/`.**

```json
{
  "thisYear": {"contributionCalendar": {"totalContributions": 142}},
  "calendar": {"contributionCalendar": {"weeks": [{"contributionDays": [
    {"date": "2026-10-01", "contributionCount": 1},
    {"date": "2026-10-02", "contributionCount": 0},
    {"date": "2026-10-03", "contributionCount": 2},
    {"date": "2026-10-04", "contributionCount": 1},
    {"date": "2026-10-05", "contributionCount": 3},
    {"date": "2026-10-06", "contributionCount": 1},
    {"date": "2026-10-07", "contributionCount": 0},
    {"date": "2026-10-08", "contributionCount": 0},
    {"date": "2026-10-09", "contributionCount": 0},
    {"date": "2026-10-10", "contributionCount": 0},
    {"date": "2026-10-11", "contributionCount": 4},
    {"date": "2026-10-12", "contributionCount": 2},
    {"date": "2026-10-13", "contributionCount": 1}
  ]}]}},
  "owned": {"totalCount": 16, "nodes": [
    {"isFork": false, "languages": {"edges": [{"size": 6000, "node": {"name": "TypeScript"}}, {"size": 500, "node": {"name": "CSS"}}]}},
    {"isFork": false, "languages": {"edges": [{"size": 3000, "node": {"name": "Python"}}]}},
    {"isFork": false, "languages": {"edges": [{"size": 1500, "node": {"name": "Dart"}}]}},
    {"isFork": false, "languages": {"edges": [{"size": 1000, "node": {"name": "JavaScript"}}, {"size": 400, "node": {"name": "HTML"}}]}},
    {"isFork": false, "languages": {"edges": [{"size": 300, "node": {"name": "C++"}}]}}
  ]},
  "recent": {"nodes": [
    {"name": "pane", "nameWithOwner": "Emyol/pane", "defaultBranchRef": {"target": {"history": {"nodes": [
      {"oid": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678", "messageHeadline": "pane: add widget grid persistence", "committedDate": "2026-10-12T10:00:00Z", "url": "https://github.com/Emyol/pane/commit/a1b2c3d", "author": {"user": {"login": "Emyol"}}},
      {"oid": "ffffffffffffffffffffffffffffffffffffffff", "messageHeadline": "Merge branch 'main'", "committedDate": "2026-10-12T11:00:00Z", "url": "https://github.com/Emyol/pane/commit/fffffff", "author": {"user": {"login": "Emyol"}}}
    ]}}}},
    {"name": "Emyol", "nameWithOwner": "Emyol/Emyol", "defaultBranchRef": {"target": {"history": {"nodes": [
      {"oid": "1111111111111111111111111111111111111111", "messageHeadline": "chore: refresh live profile data", "committedDate": "2026-10-13T00:00:00Z", "url": "https://github.com/Emyol/Emyol/commit/1111111", "author": {"user": null}}
    ]}}}},
    {"name": "MielPortfolio", "nameWithOwner": "Emyol/MielPortfolio", "defaultBranchRef": {"target": {"history": {"nodes": [
      {"oid": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432", "messageHeadline": "hero motion <polish> & *tweaks*", "committedDate": "2026-10-11T09:00:00Z", "url": "https://github.com/Emyol/MielPortfolio/commit/9f8e7d6", "author": {"user": {"login": "Emyol"}}}
    ]}}}},
    {"name": "KitaKo_Codebase", "nameWithOwner": "Emyol/KitaKo_Codebase", "defaultBranchRef": null},
    {"name": "BekiLang", "nameWithOwner": "Emyol/BekiLang", "defaultBranchRef": {"target": {"history": {"nodes": [
      {"oid": "4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f", "messageHeadline": "interpreter: support nested chika blocks", "committedDate": "2026-10-10T08:00:00Z", "url": "https://github.com/Emyol/BekiLang/commit/4c5d6e7", "author": {"user": {"login": "Emyol"}}}
    ]}}}}
  ]}
}
```

- [ ] **Step 2: Write the failing tests**

`tools/tests/test_build_live.py`:

```python
import io
import json
import urllib.error
from datetime import date, datetime
from pathlib import Path

import pytest

import build_live
from github_api import GitHubError, fetch_profile
from stats import END, MANILA, START, StatsView
from svg import validate

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
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tools/tests/test_build_live.py -q`
Expected: `ModuleNotFoundError: No module named 'build_live'`.

- [ ] **Step 4: Implement `tools/github_api.py`**

```python
"""One GraphQL round-trip for everything the live section needs (public data only)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime

API = 'https://api.github.com/graphql'

QUERY = """
query($login: String!, $yearStart: DateTime!) {
  user(login: $login) {
    thisYear: contributionsCollection(from: $yearStart) { contributionCalendar { totalContributions } }
    calendar: contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
    owned: repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { isFork languages(first: 20, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
    recent: repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 6,
                         orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name nameWithOwner
        defaultBranchRef { target { ... on Commit { history(first: 5) {
          nodes { oid messageHeadline committedDate url author { user { login } } }
        } } } }
      }
    }
  }
}
"""


class GitHubError(RuntimeError):
    pass


def fetch_profile(login: str, token: str, now: datetime, opener=urllib.request.urlopen) -> dict:
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    body = json.dumps({'query': QUERY, 'variables': {'login': login, 'yearStart': year_start.isoformat()}})
    request = urllib.request.Request(API, data=body.encode(), headers={
        'Authorization': f'bearer {token}', 'Content-Type': 'application/json',
        'User-Agent': f'{login}-profile-readme'})
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        raise GitHubError(f'GitHub request failed: {exc.reason}') from exc
    if payload.get('errors'):
        raise GitHubError('GitHub GraphQL errors: ' + '; '.join(e.get('message', '?') for e in payload['errors']))
    user = (payload.get('data') or {}).get('user')
    if not user:
        raise GitHubError(f'user {login} not found')
    return user
```

- [ ] **Step 5: Implement `tools/build_live.py`**

```python
"""Daily job: fetch public GitHub data, render the `gh stats` panel, refresh the README's recent block.

Everything is built and validated in memory first. Files are written only if every step succeeds.
Run: GITHUB_TOKEN=... python tools/build_live.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

from github_api import GitHubError, fetch_profile
from stats import (MANILA, Commit, StatsView, language_share, recent_commits, recent_lines,
                   replace_block, streaks)
from svg import PALETTES, ROOT, THEMES, WIDTH, document, rect, text, text_width, validate
from term import (CHROME_H, MOTION_CSS, SIZE_BODY, SIZE_SECONDARY, SIZE_SMALL, prompt_line, rise,
                  window)

LOGIN = 'Emyol'
PROFILE_REPO = 'Emyol/Emyol'
LIVE = ROOT / 'assets' / 'live'
VALUE_X = 420


def days(n: int) -> str:
    return f'{n} day' if n == 1 else f'{n} days'


def summarize(user: dict, today: date) -> tuple[StatsView, list[Commit]]:
    calendar = [(date.fromisoformat(d['date']), d['contributionCount'])
                for week in user['calendar']['contributionCalendar']['weeks']
                for d in week['contributionDays']]
    current, longest = streaks(calendar, today)
    view = StatsView(
        year=today.year,
        contributions_this_year=user['thisYear']['contributionCalendar']['totalContributions'],
        current_streak=current,
        longest_streak=longest,
        public_repos=user['owned']['totalCount'],
        languages=language_share(user['owned']['nodes']),
    )
    return view, recent_commits(user['recent']['nodes'], LOGIN, PROFILE_REPO)


def stats_panel(view: StatsView, theme: str) -> str:
    p = PALETTES[theme]
    y = CHROME_H + 62
    body = prompt_line(f'gh stats --user {LOGIN}', 48, y, p)
    rows = [
        (f'contributions ({view.year})', f'{view.contributions_this_year:,}'),
        ('current streak', days(view.current_streak)),
        ('longest streak', days(view.longest_streak)),
        ('public repos', f'{view.public_repos:,}'),
    ]
    y += 30
    for i, (label, value) in enumerate(rows):
        y += 46
        body += rise(text(label, 48, y, SIZE_SECONDARY, p['dim'])
                     + text(value, VALUE_X, y, SIZE_BODY, p['fg'], weight=700), 150 + i * 60)
    y += 60
    lang = text('languages', 48, y, SIZE_SECONDARY, p['dim'])
    end_y = y
    if view.languages:
        colors = [p['heat'][4], p['heat'][3], p['heat'][2], p['string'], p['heat'][1], p['dim']]
        bar_w = WIDTH - 40 - VALUE_X
        x = VALUE_X
        for i, ((_, pct), color) in enumerate(zip(view.languages, colors)):
            w = (VALUE_X + bar_w - x) if i == len(view.languages) - 1 else round(bar_w * pct / 100)
            lang += rect(x, y - 18, w, 18, color)
            x += w
        x, end_y = VALUE_X, y + 46
        for (name, pct), color in zip(view.languages, colors):
            label = f'{name} {pct}%'
            w = 24 + text_width(label, SIZE_SMALL) + 28
            if x > VALUE_X and x + w > WIDTH - 40:
                x, end_y = VALUE_X, end_y + 36
            lang += rect(x, end_y - 15, 14, 14, color, 3) + text(label, x + 24, end_y, SIZE_SMALL, p['fg'])
            x += w
    else:
        lang += text('no language data yet', VALUE_X, y, SIZE_SECONDARY, p['dim'])
    body += rise(lang, 150 + len(rows) * 60)
    height = int(end_y + 40)
    share = ', '.join(f'{n} {pct}%' for n, pct in view.languages) or 'none yet'
    title = (f'GitHub stats for {LOGIN}: {view.contributions_this_year:,} contributions in {view.year}, '
             f'current streak {days(view.current_streak)}, longest streak {days(view.longest_streak)}, '
             f'{view.public_repos} public repositories. Languages: {share}.')
    return document(height, title, window(height, 'gh stats', body, p), MOTION_CSS)


def render(user: dict, today: date, readme: str) -> tuple[dict[str, str], str]:
    view, commits = summarize(user, today)
    svgs = {f'stats-{theme}.svg': stats_panel(view, theme) for theme in THEMES}
    for svg in svgs.values():
        validate(svg)
    return svgs, replace_block(readme, recent_lines(commits))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Refresh the live stats panel and recent commits.')
    parser.add_argument('--fixture', type=Path, help='read the GraphQL user object from JSON (tests only)')
    parser.add_argument('--readme', type=Path, default=ROOT / 'README.md')
    parser.add_argument('--out', type=Path, default=LIVE)
    parser.add_argument('--today', type=date.fromisoformat, help='override today (YYYY-MM-DD, Manila)')
    args = parser.parse_args(argv)
    now = datetime.now(MANILA)
    today = args.today or now.date()
    try:
        if args.fixture:
            user = json.loads(args.fixture.read_text(encoding='utf-8'))
        else:
            user = fetch_profile(LOGIN, os.environ['GITHUB_TOKEN'], now)
        svgs, readme = render(user, today, args.readme.read_text(encoding='utf-8'))
    except (GitHubError, KeyError, TypeError, ValueError, ET.ParseError, OSError) as exc:
        print(f'build_live: nothing written: {exc!r}', file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    for name, svg in svgs.items():
        (args.out / name).write_text(svg, encoding='utf-8', newline='\n')
    args.readme.write_text(readme, encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest tools/tests -q`
Expected: `65 passed`.

- [ ] **Step 7: Commit**

```bash
git add tools/github_api.py tools/build_live.py tools/tests/fixtures/user.json tools/tests/test_build_live.py
git commit -m "feat: render gh stats panel and recent commits from GitHub data" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: New README, seeded with real data, old art removed

**Files:**
- Modify: `README.md` (full rewrite)
- Create: `tools/tests/test_readme.py`, `assets/live/stats-dark.svg`, `assets/live/stats-light.svg` (from real data)
- Delete: `tools/build_visuals.py`, `assets/silver-field.svg`, `assets/kitako.svg`, `assets/icare.svg`, `assets/bekilang.svg`, `assets/citysense.svg`, `assets/toolkit.svg`

**Interfaces:**
- Consumes: static file names from Task 4, `stats-{t}.svg` from Task 6, `START`/`END` from `stats.py`.
- Produces: the published page. The snake URLs point to the `output` branch that Task 8's workflow creates.

- [ ] **Step 1: Write the failing test**

`tools/tests/test_readme.py`:

```python
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
    assert len(pictures) == 11
    for block in pictures:
        assert 'media="(prefers-color-scheme: dark)"' in block
        alt = re.search(r'<img [^>]*alt="([^"]*)"', block)
        assert alt and alt.group(1).strip(), block


def test_recent_markers_appear_once():
    assert README.count(START) == 1 and README.count(END) == 1


def test_contact_links():
    for url in ['https://project-miel.vercel.app', 'https://www.linkedin.com/in/amiel-acu%C3%B1a',
                'mailto:acunaamieljosiah@gmail.com']:
        assert url in README


def test_old_art_is_gone():
    for old in ['silver-field', 'toolkit.svg', 'assets/kitako.svg']:
        assert old not in README
    assert not (ROOT / 'tools' / 'build_visuals.py').exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tools/tests/test_readme.py -q`
Expected: FAIL (the old README has no `<picture>` blocks and still references `silver-field`).

- [ ] **Step 3: Rewrite `README.md`**

```markdown
<!-- Art in assets/static is built by `python tools/build_static.py`; assets/live and the recent block are refreshed daily by .github/workflows/profile.yml. -->

<a href="https://project-miel.vercel.app">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/static/hero-dark.svg">
    <img alt="$ whoami: Amiel Acuña. Student leader building web and mobile software at FEU Tech, Manila." src="assets/static/hero-light.svg" width="100%">
  </picture>
</a>

**[Portfolio](https://project-miel.vercel.app) · [LinkedIn](https://www.linkedin.com/in/amiel-acu%C3%B1a) · [Email](mailto:acunaamieljosiah@gmail.com)**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/static/work-header-dark.svg">
  <img alt="$ ls ~/work --pinned" src="assets/static/work-header-light.svg" width="100%">
</picture>

<a href="https://github.com/Emyol/KitaKo_Codebase">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/static/work-kitako-dark.svg">
    <img alt="01 KitaKo: find a photo in your own words. Flutter, Dart, ONNX Runtime." src="assets/static/work-kitako-light.svg" width="100%">
  </picture>
</a>

[**KitaKo**](https://github.com/Emyol/KitaKo_Codebase): On-device semantic photo search with Taglish support.

<a href="https://github.com/Emyol/iCARE-Reservation">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/static/work-icare-dark.svg">
    <img alt="02 iCARE Reservation: room bookings for 700+ STEM students. Next.js, React, JavaScript." src="assets/static/work-icare-light.svg" width="100%">
  </picture>
</a>

[**iCARE Reservation**](https://github.com/Emyol/iCARE-Reservation): AVR and Training Room scheduling with JavaScript, React, and Next.js.

<a href="https://github.com/Emyol/BekiLang">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/static/work-bekilang-dark.svg">
    <img alt="03 BekiLang: Swardspeak, compiled. Python, Flask." src="assets/static/work-bekilang-light.svg" width="100%">
  </picture>
</a>

[**BekiLang**](https://github.com/Emyol/BekiLang): A Swardspeak-inspired programming language with a Python compiler and interpreter, and a Flask web interface.

<a href="https://github.com/Emyol/city-sense">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/static/work-citysense-dark.svg">
    <img alt="04 CitySense: urban heat and greenspace from orbit. TypeScript, React, Leaflet, Vite." src="assets/static/work-citysense-light.svg" width="100%">
  </picture>
</a>

[**CitySense**](https://github.com/Emyol/city-sense): Earth observation layers for exploring urban heat, greenspace, water, and population.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/static/stack-dark.svg">
  <img alt="neofetch. Languages: TypeScript, JavaScript, Python, Dart, C++. Web: Next.js, React, Tailwind CSS, shadcn/ui, GSAP. Mobile: Flutter, ONNX Runtime. Data: Supabase, Prisma, Flask, pandas, scikit-learn. Testing: Playwright, Vitest. Tools: Git, Vercel, Figma, Leaflet." src="assets/static/stack-light.svg" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/live/stats-dark.svg">
  <img alt="$ gh stats: contributions this year, current and longest streak, public repositories and language share. Refreshed daily." src="assets/live/stats-light.svg" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/static/graph-header-dark.svg">
  <img alt="$ git log --graph --all" src="assets/static/graph-header-light.svg" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Emyol/Emyol/output/github-snake-dark.svg">
  <img alt="A snake eating the contribution graph. Regenerated daily." src="https://raw.githubusercontent.com/Emyol/Emyol/output/github-snake.svg" width="100%">
</picture>

**`$ git log --oneline -3`**

<!-- recent:start -->
<!-- recent:end -->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/static/footer-dark.svg">
  <img alt="$ exit: salamat sa pagbisita, thanks for stopping by." src="assets/static/footer-light.svg" width="100%">
</picture>
```

- [ ] **Step 4: Delete the old art**

```bash
git rm -q tools/build_visuals.py assets/silver-field.svg assets/kitako.svg assets/icare.svg assets/bekilang.svg assets/citysense.svg assets/toolkit.svg
```

- [ ] **Step 5: Seed the live section with REAL data**

```bash
GITHUB_TOKEN="$(gh auth token)" python tools/build_live.py && echo OK
sed -n '/recent:start/,/recent:end/p' README.md
```

Expected: `OK`, and three real commit lines between the markers. If it prints `build_live: nothing written: …`, fix the cause. Do **not** fall back to `--fixture`, because fixture numbers must never be published. If the GraphQL error mentions a schema field, check the field name against https://docs.github.com/graphql and fix `QUERY`, then re-run Task 6's tests.

- [ ] **Step 6: Run the whole suite**

Run: `python -m pytest tools/tests -q`
Expected: `70 passed`.

- [ ] **Step 7: Commit**

```bash
git add README.md tools/tests/test_readme.py assets/live
git commit -m "feat: switch profile README to the terminal layout" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Daily refresh workflow

**Files:**
- Create: `.github/workflows/profile.yml`, `tools/tests/test_workflow.py`

**Interfaces:**
- Consumes: `tools/build_live.py` CLI (no flags in CI), `tools/requirements.txt`. The snake palette values come from Global Constraints.
- Produces: the `output` branch with `github-snake.svg` and `github-snake-dark.svg`, and daily `chore: refresh live profile data` commits on `main`.

- [ ] **Step 1: Write the failing test**

`tools/tests/test_workflow.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tools/tests/test_workflow.py -q`
Expected: `FileNotFoundError` for `profile.yml`.

- [ ] **Step 3: Check the publish action's input names**

Run: `curl -s https://raw.githubusercontent.com/crazy-max/ghaction-github-pages/v5.0.0/action.yml | grep -nE '^  (target_branch|build_dir):'`
Expected: both inputs listed. If v5 renamed either, use the new names in Step 4 and tell the user.

- [ ] **Step 4: Write `.github/workflows/profile.yml`**

```yaml
name: Refresh profile

on:
  schedule:
    - cron: "0 16 * * *" # 00:00 in Manila (UTC+8)
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: refresh-profile
  cancel-in-progress: false

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Generate contribution snake
        uses: Platane/snk@v3
        with:
          github_user_name: ${{ github.repository_owner }}
          outputs: |
            dist/github-snake.svg?color_snake=#1f7a43&color_dots=#e3e9e4,#b9dcc4,#7cc296,#3f9a62,#1f7a43
            dist/github-snake-dark.svg?color_snake=#7ee2a0&color_dots=#141a16,#1d3a28,#2b6a44,#4fa36e,#7ee2a0

      - name: Publish snake to the output branch
        uses: crazy-max/ghaction-github-pages@v5
        with:
          target_branch: output
          build_dir: dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
          cache-dependency-path: tools/requirements.txt

      - run: python -m pip install -r tools/requirements.txt

      - name: Build stats panel and recent commits
        run: python tools/build_live.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Commit refreshed data
        run: |
          git add assets/live README.md
          if git diff --cached --quiet; then
            echo "Nothing changed."
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git commit -m "chore: refresh live profile data"
          git push
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tools/tests -q`
Expected: `74 passed`.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/profile.yml tools/tests/test_workflow.py
git commit -m "ci: refresh snake, stats and recent commits daily" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Preview contact sheets and visual review with the user

**Files:**
- Create: `tools/preview.py`

**Interfaces:**
- Consumes: `assets/static/*-{t}.svg`, `assets/live/stats-{t}.svg`.
- Produces: `previews/sheet-{dark|light}-{830|360}.png` (git-ignored).

- [ ] **Step 1: Install the browser**

Run: `python -m playwright install chromium`

- [ ] **Step 2: Write `tools/preview.py`**

```python
"""Render every built SVG, in README order, into contact sheets for visual review.

Run: python tools/preview.py   → previews/sheet-{dark,light}-{830,360}.png
Reduced motion is emulated, so each sheet shows the final frame (what static renderers see).
"""
from __future__ import annotations

from playwright.sync_api import sync_playwright

from svg import ROOT, THEMES

OUT = ROOT / 'previews'
GITHUB_BG = {'dark': '#0d1117', 'light': '#ffffff'}
ORDER = ['static/hero', 'static/work-header', 'static/work-kitako', 'static/work-icare',
         'static/work-bekilang', 'static/work-citysense', 'static/stack', 'live/stats',
         'static/graph-header', 'static/footer']
WIDTHS = (830, 360)


def sheet_html(theme: str, width: int) -> str:
    images = ''.join(f'<img src="{(ROOT / "assets" / f"{stem}-{theme}.svg").as_uri()}">' for stem in ORDER)
    return (f'<!doctype html><meta charset="utf-8"><style>body{{margin:0;padding:20px;'
            f'background:{GITHUB_BG[theme]}}}main{{width:{width}px;display:grid;gap:12px}}'
            f'img{{width:100%;display:block}}</style><main>{images}</main>')


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for theme in THEMES:
            for width in WIDTHS:
                page = browser.new_page(viewport={'width': width + 40, 'height': 900},
                                        reduced_motion='reduce', color_scheme=theme)
                html = OUT / f'sheet-{theme}-{width}.html'
                html.write_text(sheet_html(theme, width), encoding='utf-8')
                page.goto(html.as_uri())
                page.wait_for_load_state('load')
                page.screenshot(path=str(OUT / f'sheet-{theme}-{width}.png'), full_page=True)
                page.close()
        browser.close()
    print(f'Wrote {len(THEMES) * len(WIDTHS)} contact sheets to {OUT}')


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Render and inspect**

Run: `python tools/preview.py`
Expected: `Wrote 4 contact sheets to …/previews`.

Open all four PNGs (use the Read tool on each) and check each item. Fix in `build_static.py` / `build_live.py` and re-render until every item passes:
- No text is clipped or overlaps another element, in any image, at 830 px or 360 px.
- At 360 px the project names and hero name are still readable. Secondary text may be small, but the Markdown lines under the strips carry the same content.
- Icons are tinted (mint on dark, deep green on light), not black or blank.
- The neofetch rows wrap cleanly and the sun isn't overlapped by the key column.
- The light sheet has no dark slabs, and the dark sheet has no light slabs.

- [ ] **Step 4: Check the animation by eye**

Open `assets/static/hero-dark.svg` and `assets/static/stack-dark.svg` directly in a browser. The hero types `whoami`, the name rises, `cat role.txt` types, the role rises, and the cursor appears and blinks, all finished by about 2.5 s. Nothing else moves afterwards.

- [ ] **Step 5: User checkpoint**

Show the user the four contact sheets and ask for approval before shipping. Apply any requested changes by editing the builders, re-running Steps 3–4 and `python -m pytest tools/tests -q`.

- [ ] **Step 6: Commit**

```bash
python tools/build_static.py
python -m pytest tools/tests -q
git add tools/preview.py assets/static
git commit -m "chore: add preview contact sheets for visual review" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Ship to `Emyol/Emyol` and verify live

**Files:** none (git and GitHub operations).

**Interfaces:**
- Consumes: the finished branch, and `gh` authenticated as `Emyol` (verified during planning).
- Produces: the live profile at https://github.com/Emyol.

- [ ] **Step 1: Final local verification**

```bash
python -m pytest tools/tests -q
git status --short
git log --oneline origin/main..HEAD
```

Expected: `74 passed`, a clean tree, and the branch commits listed on top of `origin/main`.

- [ ] **Step 2: Ask the user to confirm the push**

Pushing publishes the profile. Show the commit list from Step 1 and ask: "Push these commits to `Emyol/Emyol` `main` now?" Continue only on an explicit yes.

- [ ] **Step 3: Push**

```bash
git fetch origin main
git rebase origin/main   # no-op unless GitHub moved; re-run tests if it did
git push origin HEAD:main
```

- [ ] **Step 4: Run the workflow and watch it**

```bash
gh workflow run profile.yml -R Emyol/Emyol --ref main
sleep 5
gh run watch -R Emyol/Emyol "$(gh run list -R Emyol/Emyol -w profile.yml -L 1 --json databaseId -q '.[0].databaseId')" --exit-status
```

Expected: the run finishes green. On failure: `gh run view -R Emyol/Emyol --log-failed`, then fix, test, commit, push and re-run.

- [ ] **Step 5: Confirm the snake exists and pull the bot commit**

```bash
gh api "repos/Emyol/Emyol/contents/github-snake-dark.svg?ref=output" -q .name
git pull --rebase origin main
```

Expected: `github-snake-dark.svg`.

- [ ] **Step 6: Check the live profile**

Open https://github.com/Emyol with GitHub's appearance set to light, then to dark, then on a phone (or with the browser's device emulation at 390 px). Confirm: the hero animates once, every image is the right theme variant, the snake loads, the stats show real numbers, the recent commits are real, and all links work. Report the result to the user, with any defects.

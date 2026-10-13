"""Render every built SVG, in README order, into contact sheets for visual review.

Run: python tools/preview.py   → previews/sheet-{dark,light}-{830,360}.png
Images are loaded in a tall viewport (so every one paints and starts its intro at load) and the
page waits past the longest intro (3.2 s), so each sheet shows the settled final frame.
Reduced motion is NOT emulated here: Playwright's emulation does not reach SVGs loaded via <img>.
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
SETTLE_MS = 4500


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
                page = browser.new_page(viewport={'width': width + 40, 'height': 4000},
                                        color_scheme=theme)
                html = OUT / f'sheet-{theme}-{width}.html'
                html.write_text(sheet_html(theme, width), encoding='utf-8')
                page.goto(html.as_uri())
                page.wait_for_load_state('load')
                page.wait_for_timeout(SETTLE_MS)
                height = page.evaluate('document.body.scrollHeight')
                page.screenshot(path=str(OUT / f'sheet-{theme}-{width}.png'),
                                clip={'x': 0, 'y': 0, 'width': width + 40, 'height': height})
                page.close()
        browser.close()
    print(f'Wrote {len(THEMES) * len(WIDTHS)} contact sheets to {OUT}')


if __name__ == '__main__':
    main()

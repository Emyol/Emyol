"""Build the committed section art (depth headers, the stack panel) in both GitHub themes.

Run: python tools/build_static.py   → writes assets/static/*-{dark,light}.svg
The hero and the project cards are built by tools/ocean.py.
"""
from __future__ import annotations

from svg import PALETTES, ROOT, THEMES, WIDTH, document, rect, text, text_width, validate, write
from term import CHROME_H, MOTION_CSS, SIZE_SECONDARY, SIZE_SMALL, flow, rise, window

STATIC = ROOT / 'assets' / 'static'

# neofetch layout: key column, first item column, right limit, gap between items
STACK_KEY_X = 250
STACK_ITEMS_X = 400
STACK_RIGHT = WIDTH - 30
STACK_GAP = 20
SUN_SIZE = SIZE_SMALL

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

# Section headers read as depth marks on the way down, as the site's depth gauge does.
HEADERS = {
    'work-header': ('−40 m', 'Selected work', 'seven projects, newest first'),
    'stack-header': ('−200 m', 'Toolkit', 'what I build with'),
    'graph-header': ('−240 m', 'The trench', 'a year of commits, eaten daily'),
    'footer': ('0 m', 'Back to the surface', 'salamat sa pagbisita, thanks for stopping by'),
}
HEADER_H = 96

def header(depth: str, title: str, caption: str, theme: str) -> str:
    """Transparent, so it sits on either GitHub theme: depth, title in Fraunces, caption, hairline."""
    p = PALETTES[theme]
    fg = p['fg'] if theme == 'dark' else '#1f2328'
    dim = p['dim'] if theme == 'dark' else '#59636e'
    body = text(depth, 0, 40, 15, p['prompt'], 'mono', 500, 1.2)
    body += text(title, 0, 82, 44, fg, 'serif', 800, -0.6)
    body += text(caption, WIDTH - text_width(caption, 20, 'sans', 400), 82, 20, dim, 'sans', 400)
    body += rect(0, HEADER_H - 2, WIDTH, 1, dim, extra=' fill-opacity=".35"')
    return document(HEADER_H, f'{depth}: {title}. {caption}', rise(body, 80), MOTION_CSS)


def stack_panel(theme: str) -> str:
    p = PALETTES[theme]
    top = CHROME_H + 62
    sun = ''.join(text(line, 48, top + i * 30, SUN_SIZE, p['prompt']) for i, line in enumerate(SUN))
    sun += text('miel@manila', 48, top + len(SUN) * 30 + 30, SIZE_SMALL, p['dim'])
    body = rise(sun, 100)  # the title bar already reads "neofetch"
    y = top
    for i, (key, items) in enumerate(STACK):
        row = text(key, STACK_KEY_X, y, SIZE_SECONDARY, p['prompt'], weight=700)
        items_svg, rows = flow(items, STACK_ITEMS_X, STACK_RIGHT, y, p, gap=STACK_GAP)
        body += rise(row + items_svg, 150 + i * 60)
        y += rows * 44 + 14
    swatches = ''.join(rect(STACK_KEY_X + i * 34, y, 26, 14, color, 3)
                       for i, color in enumerate([*p['heat'], p['string']]))
    body += rise(swatches, 150 + len(STACK) * 60)
    height = int(max(y + 50, top + (len(SUN) + 1) * 30 + 40))
    title = 'neofetch: ' + '; '.join(f"{key}: {', '.join(label for _, label in items)}"
                                     for key, items in STACK)
    return document(height, title, window(height, 'neofetch', body, p), MOTION_CSS)


def build_all() -> dict[str, str]:
    files = {}
    for theme in THEMES:
        for stem, (depth, title, caption) in HEADERS.items():
            files[f'{stem}-{theme}.svg'] = header(depth, title, caption, theme)
        files[f'stack-{theme}.svg'] = stack_panel(theme)
    return files


def all_copy() -> list[tuple[str, int, str]]:
    copy = [('mono', 400, 'neofetch'), ('mono', 400, 'miel@manila'), ('mono', 400, '0123456789')]
    copy += [('mono', 500, d) for d, _, _ in HEADERS.values()]
    copy += [('serif', 800, t) for _, t, _ in HEADERS.values()]
    copy += [('sans', 400, c) for _, _, c in HEADERS.values()]
    copy += [('mono', 700, key) for key, _ in STACK]
    copy += [('mono', 400, label) for _, items in STACK for _, label in items]
    copy += [('mono', 400, line) for line in SUN]
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

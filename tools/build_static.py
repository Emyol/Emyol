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

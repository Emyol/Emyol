"""The Dive ocean as SVGs a README can play: the hero and one glass card per project.

Run: python tools/ocean.py   → writes assets/dive/hero.svg and assets/dive/work-<slug>.svg

Ported from the portfolio's ocean (components/dive/ocean-core.js in MielPortfolio). GitHub runs no
JavaScript in a README, so the water is pre-computed frames shown in turn by CSS, and the whale shark is
a tail-beat sprite moved one character cell at a time by CSS keyframes. Everything is deterministic, so a
rebuild gives byte-identical files. These images are dark in both GitHub themes, like the site.
"""
from __future__ import annotations

import base64
import io
import math
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from svg import FONTS, ROOT, TOOLS, text, text_width

OUT = ROOT / 'assets' / 'dive'
SHOTS = TOOLS / 'shots'
W = 1200
MAX_BYTES = 1_200_000  # the hero is ~0.9 MB raw, ~75 KB gzipped

BG, INK, ACCENT, MUTE, BODY = '#070707', '#ececec', '#2997ff', '#9d9d9d', '#c9c9c9'
DIM_OP, FROST_OP, RIM_OP = 0.34, 0.16, 0.6
RAMP = ' .:-=+*#%@'
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

PROJECTS = [
    {'slug': 'kitako', 'title': 'KitaKo', 'meta': 'Undergraduate thesis · 2026', 'window': 'KitaKo · project site',
     'description': 'Private semantic image search that understands Taglish queries and runs entirely on-device.',
     'stack': ['Flutter', 'Dart', 'ONNX Runtime', 'SigLIP-2', 'IVF-PQ'],
     'code': 'https://github.com/Emyol/KitaKo_Codebase', 'live': ''},
    {'slug': 'homestead', 'title': 'Homestead', 'meta': 'NASA Space Apps Challenge · 2026', 'window': 'Homestead · mission setup',
     'description': 'A co-op space-mission game: scavenge parts, build a spacecraft, fly it together, and learn which design choice decided the run.',
     'stack': ['JavaScript', 'TypeScript', 'Canvas 2D', 'WebRTC', 'PeerJS'],
     'code': 'https://github.com/TadeyRuk/Homestead', 'live': 'https://seedlign.itch.io/homestead'},
    {'slug': 'eventflow', 'title': 'EventFlow', 'meta': 'n8n Buildathon finals · 2026', 'window': 'EventFlow · certificate',
     'description': 'Event lifecycle automation on n8n that checks people in by token and certifies only those who attended and submitted.',
     'stack': ['n8n', 'JavaScript', 'Google Sheets', 'Gmail', 'Notion'],
     'code': 'https://github.com/Seedlign/eventflow-n8n', 'live': ''},
    {'slug': 'kislap', 'title': 'Kislap', 'meta': 'AppBuildersPH Hackathon · 2026', 'window': 'Kislap · reading game',
     'description': 'A reading game for Filipino children that listens to each sentence with a speech model running on the child’s own device.',
     'stack': ['TypeScript', 'React', 'Transformers.js', 'Whisper', 'PWA'],
     'code': 'https://github.com/Romeo-04/kislap', 'live': 'https://romeo-04.github.io/kislap/'},
    {'slug': 'icare', 'title': 'iCARE Reservation', 'meta': 'Internal tooling · 2026', 'window': 'iCARE · Availability',
     'description': 'A shared-facility portal that reduces booking friction and catches room conflicts before submission.',
     'stack': ['Next.js', 'JavaScript', 'Node test runner'],
     'code': 'https://github.com/Emyol/iCARE-Reservation', 'live': ''},
    {'slug': 'bekilang', 'title': 'BekiLang', 'meta': 'Domain-specific language · 2026', 'window': 'BekiLang Studio',
     'description': 'A working programming language and web playground built around Philippine Swardspeak.',
     'stack': ['Python', 'Compilers', 'Interpreters'],
     'code': 'https://github.com/Emyol/BekiLang', 'live': ''},
    {'slug': 'citysense', 'title': 'CitySense', 'meta': 'NASA Space Apps Challenge · 2025', 'window': 'CitySense',
     'description': 'A planning cockpit that combines live environmental layers with an AI-assisted policy workflow.',
     'stack': ['TypeScript', 'Vite', 'Leaflet', 'NASA GIBS', 'DeepSeek R1'],
     'code': 'https://github.com/Emyol/city-sense', 'live': ''},
]

HERO_TITLE = ('Hi, I’m Miel. Amiel Josiah Acuña, software engineer at FEU Tech, Manila. '
              'I build software and enjoy working with people.')


def card_depth(index: int) -> str:
    return f'−{60 + index * 20} m'


def clamp(v, a, b):
    return min(b, max(a, v))


def _frac(v):
    return v - math.floor(v)


def _hash1(x, y, s):
    return _frac(math.sin(x * 127.1 + y * 311.7 + s * 74.37) * 43758.5453123)


def noise(x, y, s):
    """Value noise, as in ocean-core.js."""
    x0, y0 = math.floor(x), math.floor(y)
    tx, ty = x - x0, y - y0
    ux, uy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = _hash1(x0, y0, s) * (1 - ux) + _hash1(x0 + 1, y0, s) * ux
    b = _hash1(x0, y0 + 1, s) * (1 - ux) + _hash1(x0 + 1, y0 + 1, s) * ux
    return a * (1 - uy) + b * uy


def hash2(a, b):
    h = ((a * 374761393) & 0xFFFFFFFF) ^ ((b * 668265263) & 0xFFFFFFFF)
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967295


def smooth(x):
    return x * x * (3 - 2 * x)


def wrap(value, size, width, family='sans', weight=400):
    lines, cur = [], ''
    for word in value.split():
        trial = (cur + ' ' + word).strip()
        if cur and text_width(trial, size, family, weight) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


class Grid:
    def __init__(self, h, cols):
        self.h, self.cols = h, cols
        self.cw = W / cols
        self.chh = self.cw * 1.7
        self.rows = math.ceil(h / self.chh)


def rows_svg(layers, cw, chh):
    """layers: (fill, opacity, row strings). One <text> per non-empty row, stretched to the grid width."""
    out = []
    for fill, op, rows in layers:
        body = []
        for r, s in enumerate(rows):
            t = s.rstrip()
            if not t.strip():
                continue
            body.append(f'<text y="{(r + 0.78) * chh:.1f}" textLength="{len(t) * cw:.1f}">{escape(t)}</text>')
        if body:
            o = f' fill-opacity="{op}"' if op < 1 else ''
            out.append(f'<g fill="{fill}"{o}>{"".join(body)}</g>')
    return ''.join(out)


def svg_doc(h, title, css, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{h}" '
            f'viewBox="0 0 {W} {h}" role="img"><title>{escape(title)}</title><style>{css}</style>{body}</svg>')


def text_mask(value, g, top_row, n_rows):
    """Coverage 0..1 per cell of `value` in Fraunces, fitted to the width and centred."""
    scale = 4
    img = Image.new('L', (W * scale, int(n_rows * g.chh * scale)), 0)
    dr = ImageDraw.Draw(img)

    def font(px):
        f = ImageFont.truetype(str(FONTS['serif']), int(px * scale))
        f.set_variation_by_axes([144, 800, 0, 1])  # opsz, wght, SOFT, WONK
        return f

    b0 = dr.textbbox((0, 0), value, font=font(100))
    size = min(100 * W * 0.86 / ((b0[2] - b0[0]) / scale), 100 * n_rows * g.chh * 0.92 / ((b0[3] - b0[1]) / scale))
    f = font(size)
    bb = dr.textbbox((0, 0), value, font=f)
    dr.text(((img.width - (bb[2] - bb[0])) / 2 - bb[0], (img.height - (bb[3] - bb[1])) / 2 - bb[1]), value, font=f, fill=255)
    px = img.resize((g.cols, n_rows), Image.BOX).load()
    return {(r + top_row, c): px[c, r] / 255 for r in range(n_rows) for c in range(g.cols) if px[c, r] > 6}


# ---------- whale shark ----------
def shark_alpha(L, phase, facing, cw, chh, sub=3):
    """Alpha per cell of the shark seen from above, head at the origin; facing -1 swims left."""
    N, sp = 28, L / 28
    P = []
    for i in range(N):
        u = i / (N - 1)
        sway = math.sin(phase - u * 5) * L * 0.04 * u * u
        w = L * (0.012 + 0.105 * ((0.8 + 0.2 * (u / 0.14)) if u < 0.14 else (1 - (u - 0.14) / 0.86) ** 1.2))
        P.append((-facing * i * sp, sway, w))
    polys = []
    for side in (-1, 1):
        a, b, c = P[5], P[9], P[11]
        reach = L * 0.19
        polys.append([(a[0], a[1] + side * a[2] * 0.7), (c[0], c[1] + side * (c[2] + reach)), (b[0], b[1] + side * b[2] * 0.6)])
        e, gg = P[N - 1], P[N - 4]
        span = L * (0.1 if side < 0 else 0.06)
        polys.append([(gg[0], gg[1]), (e[0] - facing * L * 0.05, e[1] + side * span), (e[0], e[1])])
    dot = max(cw * 0.5, L * 0.009)
    spots = [(P[i][0], P[i][1] + k * P[i][2]) for i in range(1, N - 7) for k in (-0.58, 0, 0.58)
             if not (i + (1 if k == 0 else 0)) % 2]

    def in_tri(px, py, t):
        (x1, y1), (x2, y2), (x3, y3) = t
        d1 = (px - x2) * (y1 - y2) - (x1 - x2) * (py - y2)
        d2 = (px - x3) * (y2 - y3) - (x2 - x3) * (py - y3)
        d3 = (px - x1) * (y3 - y1) - (x3 - x1) * (py - y1)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

    xs = [p[0] for p in P]
    c0, c1 = math.floor((min(xs) - L * 0.1) / cw), math.ceil((max(xs) + L * 0.1) / cw)
    r0, r1 = math.floor(-L * 0.35 / chh), math.ceil(L * 0.35 / chh)
    cells = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            acc = 0.0
            for sy in range(sub):
                for sx in range(sub):
                    px, py = (c + (sx + 0.5) / sub) * cw, (r + (sy + 0.5) / sub) * chh
                    if not (any((px - x) ** 2 + (py - y) ** 2 <= w * w for x, y, w in P) or any(in_tri(px, py, t) for t in polys)):
                        continue
                    spot = any((px - x) ** 2 + (py - y) ** 2 <= dot * dot for x, y in spots)
                    acc += 0.8 * (0.38 if spot else 1)
            a = acc / (sub * sub)
            if a > 0.06:
                cells[(r, c)] = a
    return cells


def shark_char(a):
    v = 0.3 + (a - 0.3) / 0.7 * 0.7 if a >= 0.3 else a
    return RAMP[round(clamp(v, 0, 1) * 9)], a > 0.3


# ---------- hero ----------
def hero() -> str:
    H = 620
    g = Grid(H, 150)
    FPS, SECS = 8, 8
    F = FPS * SECS
    seed = 417.0
    quiet_top = 480  # the copy sits below this; the water fades out above it
    mask = text_mask('Hi, I’m Miel.', g, 2, 19)
    rip = {'t': 1.2, 'x': W * 0.7, 'y': H * 0.3}
    loop_r = 0.11  # the water's noise is sampled around a small circle, so the loop is seamless
    frames = []
    for f in range(F):
        t = f / FPS
        ph = 2 * math.pi * f / F
        ox_n, oy_n = loop_r * math.cos(ph), loop_r * math.sin(ph)
        snow = f * g.rows / F
        dim_rows, lit_rows, acc_rows = [], [], []
        for r in range(g.rows):
            y = (r + 0.5) * g.chh
            d_, l_, a_ = [' '] * g.cols, [' '] * g.cols, [' '] * g.cols
            for c in range(g.cols):
                x = (c + 0.5) * g.cw
                cloud = (noise(c * 0.07 + ox_n * 3, r * 0.11 + oy_n * 3, seed) * 0.62
                         + noise(c * 0.19 - ox_n * 4, r * 0.27 + oy_n * 4, seed + 31) * 0.38)
                v = clamp((cloud - 0.45) * 2.4, 0, 1) * 0.42 * (1 - smooth(clamp((y - 400) / 80, 0, 1)))
                sn = hash2(c, math.floor(r + snow) % g.rows)
                if sn > 0.9955:
                    v = max(v, 0.2 + (sn - 0.9955) * 140)
                crest, ox, oy, lit = 0.0, 0.0, 0.0, False
                age = t - rip['t']
                if 0 <= age < 2.4:
                    dist = math.hypot(x - rip['x'], y - rip['y']) or 1
                    q = (dist - age * 560) / 44
                    crest = 0.7 * math.exp(-age * 1.5) * math.exp(-q * q)
                    push = crest * q * 2.6 * g.cw
                    ox, oy = (x - rip['x']) / dist * push, (y - rip['y']) / dist * push
                m = mask.get((round(r - oy / g.chh), round(c - ox / g.cw)), 0)
                if m > 0.03:
                    v = max(v, m * (0.74 + 0.26 * noise(c * 0.21 + ox_n * 6, r * 0.33 + oy_n * 6, seed + 7)))
                    lit = m > 0.25
                if y > quiet_top - 8 and crest < 0.25:
                    continue
                ch = RAMP[round(clamp(v + crest, 0, 1) * 9)]
                if ch == ' ':
                    continue
                (a_ if crest > 0.22 else l_ if lit else d_)[c] = ch
            dim_rows.append(''.join(d_))
            lit_rows.append(''.join(l_))
            acc_rows.append(''.join(a_))
        frames.append(rows_svg([(INK, DIM_OP, dim_rows), (INK, 1, lit_rows), (ACCENT, 1, acc_rows)], g.cw, g.chh))

    # Tail-beat sprites. Each carries a background silhouette, so the shark hides the water under it.
    L, BEAT, BEAT_S = 400, 12, 1.96
    sprites = {}
    for facing in (-1, 1):
        sp = []
        for b in range(BEAT):
            cells = shark_alpha(L, 2 * math.pi * b / BEAT, facing, g.cw, g.chh)
            rmin, cmin = min(r for r, _ in cells), min(c for _, c in cells)
            nr = max(r for r, _ in cells) - rmin + 1
            nc = max(c for _, c in cells) - cmin + 1
            dim = [[' '] * nc for _ in range(nr)]
            lit = [[' '] * nc for _ in range(nr)]
            sil = []
            for (r, c), a in sorted(cells.items()):
                ch, is_lit = shark_char(a)
                if a > 0.15:
                    sil.append(f'M{c * g.cw:.1f} {r * g.chh:.1f}h{g.cw + .3:.1f}v{g.chh + .3:.1f}h{-g.cw - .3:.1f}z')
                if ch != ' ':
                    (lit if is_lit else dim)[r - rmin][c - cmin] = ch
            sp.append(f'<path fill="{BG}" d="{"".join(sil)}"/>'
                      f'<g transform="translate({cmin * g.cw:.1f} {rmin * g.chh:.1f})">'
                      + rows_svg([(INK, DIM_OP, [''.join(x) for x in dim]), (INK, 1, [''.join(x) for x in lit])], g.cw, g.chh)
                      + '</g>')
        sprites[facing] = sp

    # Swim left through the lower water, then back right a little lower. Positions snap to whole cells.
    SWIM = 30.0
    span = W + 2 * L * 1.15
    keys = []
    steps = 240
    for i in range(steps):
        u = i / steps
        if u < 0.5:
            lu = u * 2
            x = W + L * 0.25 - lu * span
            y = 352 + math.sin(lu * math.pi * 2) * 10
        else:
            lu = (u - 0.5) * 2
            x = -L * 0.25 + lu * span
            y = 380 + math.sin(lu * math.pi * 2 + 1) * 10
        keys.append((u, round(x / g.cw) * g.cw, round(y / g.chh) * g.chh))
    total = SWIM * 2
    kf = ''.join(f'{u * 100:.3f}%{{transform:translate({x:.1f}px,{y:.1f}px)}}' for u, x, y in keys)
    start = f'translate({keys[0][1]:.1f}px,{keys[0][2]:.1f}px)'
    css = (f'text{{font-family:{MONO};font-size:{g.chh * 0.86:.1f}px;white-space:pre}}'
           f'.f,.b{{opacity:0}}.f0,.b0{{opacity:1}}'
           f'.f{{animation:fr {SECS}s step-end infinite}}@keyframes fr{{0%{{opacity:1}}{100 / F:.4f}%{{opacity:0}}}}'
           f'.b{{animation:bt {BEAT_S}s step-end infinite}}@keyframes bt{{0%{{opacity:1}}{100 / BEAT:.4f}%{{opacity:0}}}}'
           f'.swim{{transform:{start};animation:swim {total}s step-end infinite}}'
           f'@keyframes swim{{{kf}100%{{transform:{start}}}}}'
           f'.leg0{{animation:l0 {total}s step-end infinite}}.leg1{{opacity:0;animation:l1 {total}s step-end infinite}}'
           '@keyframes l0{0%{opacity:1}50%{opacity:0}}@keyframes l1{0%{opacity:0}50%{opacity:1}}'
           # Reduced motion (or no CSS animation): the first frame, the first beat, the starting place.
           '@media (prefers-reduced-motion:reduce){.f,.b,.swim,.leg0,.leg1{animation:none}}')

    water = ''.join(f'<g class="f{" f0" if i == 0 else ""}" style="animation-delay:{i / FPS - SECS:.3f}s">{fr}</g>'
                    for i, fr in enumerate(frames))
    shark = ''
    for leg, facing in ((0, -1), (1, 1)):
        beats = ''.join(f'<g class="b{" b0" if b == 0 else ""}" style="animation-delay:{b * BEAT_S / BEAT - BEAT_S:.3f}s">{s}</g>'
                        for b, s in enumerate(sprites[facing]))
        shark += f'<g class="leg{leg}">{beats}</g>'
    shark = f'<g class="swim">{shark}</g>'

    label = 'AMIEL JOSIAH ACUÑA  ·  SOFTWARE ENGINEER  ·  FEU TECH, MANILA'
    lw = text_width(label, 15, 'mono', 500, 1.8)
    copy = text(label, (W - lw) / 2, 532, 15, MUTE, 'mono', 500, 1.8)
    a, b, sz = 'I build software ', 'and enjoy working with people.', 34
    tw = text_width(a + b, sz, 'sans', 500)
    copy += text(a, (W - tw) / 2, 582, sz, INK, 'sans', 500)
    copy += text(b, (W - tw) / 2 + text_width(a, sz, 'sans', 500), 582, sz, '#8a8a8a', 'sans', 500)
    gauge = ''.join(f'<rect x="{W - (36 if i % 4 == 0 else 26)}" y="{40 + i * 20}" width="{20 if i % 4 == 0 else 10}" '
                    f'height="1" fill="{INK}" fill-opacity=".35"/>' for i in range(12))
    gauge += text('0 m', W - 66, 46, 12, MUTE, 'mono', 500, 0.5)
    body = (f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>'
            f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{BG}"/>{water}{shark}{copy}{gauge}</g>'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{INK}" stroke-opacity=".14"/>')
    return svg_doc(H, HERO_TITLE, css, body)


# ---------- glass card ----------
def _lens_table(n=48):
    f = lambda x: (1 - (1 - clamp(x, 0, 1)) ** 4) ** 0.25  # convex squircle bezel
    out = []
    for i in range(n):
        x, dl = max(0.004, i / (n - 1)), 0.001
        a1 = math.atan((f(x + dl) - f(x - dl)) / (2 * dl))
        a2 = math.asin(math.sin(a1) / 1.5)  # Snell, air into glass n = 1.5
        out.append(f(x) * math.tan(a1 - a2))
    mx = max(out)
    return [m / mx for m in out]


LENS = _lens_table()


def lens_at(gl, x, y):
    px, py = x - gl['cx'], y - gl['cy']
    qx, qy = abs(px) - gl['hx'] + gl['rad'], abs(py) - gl['hy'] + gl['rad']
    if qx > 0 and qy > 0:
        h = math.hypot(qx, qy)
        sd, nx, ny = h - gl['rad'], qx / h, qy / h
    elif qx > qy:
        sd, nx, ny = qx - gl['rad'], 1, 0
    else:
        sd, nx, ny = qy - gl['rad'], 0, 1
    if sd >= 0:
        return None
    nx *= -1 if px < 0 else 1
    ny *= -1 if py < 0 else 1
    k = -sd / gl['bez']
    if k >= 1:
        return 1, 0, 0
    m = LENS[round(k * (len(LENS) - 1))] * gl['bez'] * 1.15
    return k, -nx * m, -ny * m


def short_url(url: str) -> str:
    return url.split('://', 1)[-1].rstrip('/')


def card(item: dict, index: int) -> str:
    H, pad = 461, 22
    g = Grid(H, 124)
    seed = 91.0 + index * 13
    gl = {'cx': W / 2, 'cy': H / 2, 'hx': W / 2 - pad, 'hy': H / 2 - pad, 'rad': 26, 'bez': 22}
    sx, sy, sw, sh = pad + 34, pad + 34, 560, 349
    dim_rows, rim_rows, frost_rows = [], [], []
    for r in range(g.rows):
        y = (r + 0.5) * g.chh
        d_, m_, f_ = [' '] * g.cols, [' '] * g.cols, [' '] * g.cols
        for c in range(g.cols):
            x = (c + 0.5) * g.cw
            if sx - 6 < x < sx + sw + 6 and sy - 6 < y < sy + sh + 6:
                continue
            lens = lens_at(gl, x, y)
            sc, sr = (c + lens[1] / g.cw, r + lens[2] / g.chh) if lens else (c, r)
            cloud = noise(sc * 0.07, sr * 0.11, seed) * 0.62 + noise(sc * 0.19, sr * 0.27, seed + 31) * 0.38
            v = clamp((cloud - 0.45) * 2.4, 0, 1) * 0.42
            if hash2(c, r) > 0.9955:
                v = max(v, 0.3)
            if lens:
                k = lens[0]
                v = v * 1.25 + 0.05 * (1 - k) if k < 1 else v * 0.7  # bright bent rim, frosted middle
            ch = RAMP[round(clamp(v, 0, 1) * 9)]
            if ch != ' ':
                (d_ if not lens else m_ if lens[0] < 1 else f_)[c] = ch
        dim_rows.append(''.join(d_))
        rim_rows.append(''.join(m_))
        frost_rows.append(''.join(f_))
    water = rows_svg([(INK, DIM_OP, dim_rows), (INK, RIM_OP, rim_rows), (INK, FROST_OP, frost_rows)], g.cw, g.chh)

    im = Image.open(SHOTS / f"{item['slug']}.jpg").convert('RGB').resize((sw * 3 // 2, (sh - 34) * 3 // 2), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=72, optimize=True, progressive=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    win = (f'<clipPath id="s"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="12"/></clipPath>'
           f'<g clip-path="url(#s)"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="#141414"/>'
           f'<image x="{sx}" y="{sy + 34}" width="{sw}" height="{sh - 34}" preserveAspectRatio="xMidYMid slice" '
           f'href="data:image/jpeg;base64,{b64}"/>'
           f'<rect x="{sx}" y="{sy + 33}" width="{sw}" height="1" fill="{INK}" fill-opacity=".1"/></g>'
           + ''.join(f'<circle cx="{sx + 18 + i * 16}" cy="{sy + 17}" r="5" fill="{INK}" fill-opacity=".22"/>' for i in range(3))
           + text(item['window'], sx + 70, sy + 22, 13, MUTE, 'mono', 400)
           + f'<rect x="{sx + .5}" y="{sy + .5}" width="{sw - 1}" height="{sh - 1}" rx="12" fill="none" stroke="{INK}" stroke-opacity=".16"/>')

    tx = sx + sw + 44
    tw = W - pad - 36 - tx
    depth = card_depth(index)
    t = text(f"{index + 1:02d} / {len(PROJECTS):02d}  ·  {item['meta'].upper()}", tx, sy + 22, 13, MUTE, 'mono', 500, 1.6)
    t += text(depth, W - pad - 36 - text_width(depth, 12, 'mono', 500), sy + 22, 12, MUTE, 'mono', 500)
    size = 68
    while text_width(item['title'], size, 'serif', 800, -0.045 * size) > tw and size > 36:
        size -= 2
    t += text(item['title'], tx - 2, sy + 98, size, INK, 'serif', 800, -0.045 * size)
    yy = sy + 146
    for line in wrap(item['description'], 19, tw):
        t += text(line, tx, yy, 19, BODY, 'sans', 400)
        yy += 28
    yy += 14
    cx = tx
    for s in item['stack']:
        cw_ = text_width(s, 13, 'mono', 500) + 22
        if cx + cw_ > tx + tw:
            cx, yy = tx, yy + 36
        t += (f'<rect x="{cx:.1f}" y="{yy}" width="{cw_:.1f}" height="26" rx="13" fill="{INK}" fill-opacity=".06" '
              f'stroke="{INK}" stroke-opacity=".16"/>')
        t += text(s, cx + 11, yy + 17.5, 13, '#d4d4d4', 'mono', 500)
        cx += cw_ + 8
    t += text(short_url(item['code']) + '  →', tx, sy + sh - 2, 15, ACCENT, 'mono', 500, 0.4)

    gx, gy, gw, gh = pad, pad, W - 2 * pad, H - 2 * pad
    glass = ('<defs><linearGradient id="gt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".075"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity=".025"/></linearGradient>'
             '<linearGradient id="gr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".7"/>'
             '<stop offset=".35" stop-color="#fff" stop-opacity=".08"/><stop offset=".7" stop-color="#fff" stop-opacity=".05"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity=".36"/></linearGradient></defs>'
             f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="26" fill="url(#gt)"/>'
             f'<rect x="{gx + .75}" y="{gy + .75}" width="{gw - 1.5}" height="{gh - 1.5}" rx="25.5" fill="none" stroke="url(#gr)" stroke-width="1.5"/>')
    body = (f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>'
            f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{BG}"/>{water}{glass}{win}{t}</g>')
    css = f'text{{font-family:{MONO};font-size:{g.chh * 0.86:.1f}px;white-space:pre}}'
    return svg_doc(H, f"{index + 1:02d} {item['title']}: {item['description']}", css, body)


def build_all() -> dict[str, str]:
    files = {'hero.svg': hero()}
    for i, item in enumerate(PROJECTS):
        files[f"work-{item['slug']}.svg"] = card(item, i)
    return files


def main() -> None:
    files = build_all()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in files.items():
        size = len(svg.encode('utf-8'))
        if size > MAX_BYTES:
            raise ValueError(f'{name} is {size} bytes; limit is {MAX_BYTES}')
        (OUT / name).write_text(svg, encoding='utf-8', newline='\n')
    print(f'Built {len(files)} ocean SVGs into {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()

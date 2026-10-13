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
    '.show{animation:show 1ms linear both}'
    '.cursor{animation:blink 1.06s steps(1) infinite}'
    '@keyframes rise{from{opacity:0;transform:translateY(6px)}}'
    '@keyframes type{from{transform:scaleX(1)}}'
    '@keyframes show{from{opacity:0}}'
    '@keyframes blink{50%{opacity:0}}'
    '@media (prefers-reduced-motion:reduce){.rise,.type,.show,.cursor{animation:none}}'
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


def show(content: str, delay_ms: int) -> str:
    """Appear instantly at `delay_ms` (no movement), e.g. a prompt just before its command types."""
    return f'<g class="show" style="animation-delay:{delay_ms}ms">{content}</g>'


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
    return show(prefix, delay_ms) + typed(line, cx, y - size, text_width(command, size), size * 1.35,
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

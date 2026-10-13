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


def test_prompt_prefix_appears_with_its_command():
    out = prompt_line('whoami', 40, 54, P, delay_ms=1050)
    assert 'class="show" style="animation-delay:1050ms"' in out


def test_static_prompt_line_has_no_motion_classes():
    assert 'class="show"' not in prompt_line('exit', 40, 54, P)


def test_show_is_disabled_under_reduced_motion():
    assert '.show' in MOTION_CSS.split('@media')[1]

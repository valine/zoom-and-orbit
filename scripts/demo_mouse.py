# SPDX-License-Identifier: GPL-2.0-or-later
"""Draw the demo's animated vector mouse indicator using Pycairo.

This is an explanatory animation, not captured input telemetry. The wheel is
pressed first, then its tread moves and arrows alternate to illustrate scrolling.
"""
import math

import cairo

WIDTH, HEIGHT = 294, 90


def rounded_rect(ctx, x, y, width, height, radius):
    ctx.new_sub_path()
    for cx, cy, start in ((x + width - radius, y + radius, -math.pi / 2),
                          (x + width - radius, y + height - radius, 0),
                          (x + radius, y + height - radius, math.pi / 2),
                          (x + radius, y + radius, math.pi)):
        ctx.arc(cx, cy, radius, start, start + math.pi / 2)
    ctx.close_path()


def draw_frame(path, time):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH * 2, HEIGHT * 2)
    ctx = cairo.Context(surface)
    ctx.scale(2, 2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    rounded_rect(ctx, 1, 1, WIDTH - 2, HEIGHT - 2, 14)
    ctx.set_source_rgba(.045, .06, .08, .94)
    ctx.fill_preserve()
    ctx.set_source_rgba(.8, .86, .93, .2)
    ctx.set_line_width(1)
    ctx.stroke()

    pressed = time >= .3
    scrolling = time >= 1.0
    accent = (.35, .82, 1.0)
    rounded_rect(ctx, 23, 12, 47, 66, 22)
    ctx.set_source_rgb(.12, .15, .19)
    ctx.fill_preserve()
    ctx.set_source_rgb(.77, .83, .9)
    ctx.set_line_width(2)
    ctx.stroke()
    # Separate the two ordinary buttons, leaving the central wheel distinct.
    for x1, y1, x2, y2 in ((46.5, 12, 46.5, 20), (23, 46, 70, 46)):
        ctx.move_to(x1, y1)
        ctx.line_to(x2, y2)
    ctx.set_source_rgb(.38, .44, .51)
    ctx.set_line_width(1.3)
    ctx.stroke()

    # Brief expanding ring makes the middle-button press legible.
    progress = (time - .3) / .45
    if 0 <= progress <= 1:
        ctx.set_source_rgba(*accent, .7 * (1 - progress))
        ctx.set_line_width(2)
        ctx.arc(46.5, 32, 11 + 10 * progress, 0, 2 * math.pi)
        ctx.stroke()
    rounded_rect(ctx, 40, 21, 13, 23, 6)
    ctx.set_source_rgb(*(accent if pressed else (.3, .36, .43)))
    ctx.fill()

    direction = 1 if int(max(0, time - 1) / 1.1) % 2 == 0 else -1
    offset = ((time - 1) * 22 * direction) % 6 if scrolling else 0
    ctx.save()
    rounded_rect(ctx, 41, 23, 11, 19, 4)
    ctx.clip()
    ctx.set_source_rgba(.045, .06, .08, .85)
    ctx.set_line_width(1.4)
    for n in range(-1, 5):
        y = 24 + n * 6 + offset
        ctx.move_to(43, y)
        ctx.line_to(50, y)
    ctx.stroke()
    ctx.restore()

    for arrow_direction, cy in ((1, 26), (-1, 61)):
        active = scrolling and direction == arrow_direction
        ctx.set_source_rgba(*(accent if active else (.5, .58, .66)),
                            .65 + .35 * math.sin(time * 14) ** 2 if active else .3)
        shift = -direction * (time * 7 % 3) if active else 0
        ctx.move_to(79, cy + arrow_direction * 4 + shift)
        ctx.line_to(84, cy - arrow_direction * 1 + shift)
        ctx.line_to(89, cy + arrow_direction * 4 + shift)
        ctx.set_line_width(2.2)
        ctx.stroke()

    ctx.select_font_face('Noto Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(18)
    ctx.set_source_rgb(.96, .97, .99)
    ctx.move_to(108, 37)
    ctx.show_text('Hold MMB')
    ctx.select_font_face('Noto Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(15)
    ctx.set_source_rgb(*(accent if scrolling else (.69, .75, .82)))
    ctx.move_to(108, 62)
    ctx.show_text('Scroll to zoom' if scrolling else 'Move to orbit')
    surface.write_to_png(str(path))


def render_sequence(directory, duration, fps=30):
    directory.mkdir()
    for frame in range(math.ceil(duration * fps)):
        draw_frame(directory / f'{frame:04d}.png', frame / fps)

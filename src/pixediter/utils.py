from pixediter import borders
from pixediter import colors
from pixediter import terminal
from pixediter.colors import Color


def draw(x: int, y: int, text: str, color: Color = colors.WHITE):
    terminal.addstr(y, x, color.colorize(text))


def draw_box(x0, y0, x1, y1, box_drawing_chars=borders.sharp, color=colors.WHITE):
    LR, UD, RD, LD, RU, LU = box_drawing_chars
    draw(x0, y0, RD, color=color)
    draw(x1, y0, LD, color=color)
    draw(x0, y1, RU, color=color)
    draw(x1, y1, LU, color=color)
    for x in range(x0 + 1, x1):
        draw(x, y0, LR, color=color)
        draw(x, y1, LR, color=color)
    for y in range(y0 + 1, y1):
        draw(x0, y, UD, color=color)
        draw(x1, y, UD, color=color)


def rect(x0: int, y0: int, x1: int, y1: int):
    """Generates coordinates on the edges of a rectangle"""
    if y0 > y1:
        y0, y1 = y1, y0
    if x0 > x1:
        x0, x1 = x1, x0

    if x0 == x1:
        for y in range(y0, y1 + 1):
            yield (x0, y)
        return

    if y0 == y1:
        for x in range(x0, x1 + 1):
            yield (x, y0)
        return

    for y in range(y0, y1 + 1):
        if y == y0 or y == y1:
            for x in range(x0, x1 + 1):
                yield (x, y)
        else:
            yield (x0, y)
            yield (x1, y)

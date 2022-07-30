from __future__ import annotations

from typing import Optional

from pixediter import colors
from pixediter import events
from pixediter.borders import Borders
from pixediter.colors import Color
from pixediter.ColorSelector import ColorSelector
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.utils import draw
from pixediter.utils import FILLED_PIXEL

from .TerminalWidget import TerminalWidget


class Palette(TerminalWidget):
    default_colors = [
        colors.BLACK,
        colors.GRAY,
        colors.WHITE,
        colors.RED,
        colors.YELLOW,
        colors.GREEN,
        colors.CYAN,
        colors.BLUE,
        colors.MAGENTA,
    ]

    def __init__(
            self,
            *,
            bbox: tuple[int, int, int, int],
            borders: Optional[Borders] = None,
            colors: list[Color],
            selector: ColorSelector
    ):
        super().__init__(bbox=bbox, borders=borders)
        self.colors: list[Color] = colors
        self.fill_empty_slots_with_random_colors()
        self.selector = selector

    def onclick(self, ev: events.MouseEvent) -> bool:
        if ev.event_type != MouseEventType.MOUSE_DOWN:
            # this allows the default handler to run when the user starts drawing
            # a shape and then releases mouse above this widget, and when user
            # continues drawing over this widget when it's located on top of draw
            # area
            return False

        color_idx = self.color_index_from_coords(ev.x, ev.y)

        if ev.button in (MouseButton.LEFT, MouseButton.MIDDLE):
            self.selector.set_color("primary", self.colors[color_idx])
        elif ev.button == MouseButton.RIGHT:
            self.selector.set_color("secondary", self.colors[color_idx])
        elif ev.button == MouseButton.CTRL_LEFT:
            self.set_color(color_idx, self.selector.primary)
        elif ev.button == MouseButton.CTRL_RIGHT:
            self.set_color(color_idx, self.selector.secondary)
        else:
            return False
        return True

    def move(self, dx: int, dy: int) -> None:
        super().move(dx, dy)

    def set_color(self, idx: int, color: Color) -> None:
        self.colors[idx] = color

    def color_index_from_coords(self, x: int, y: int) -> int:
        row = y - self.top
        col = (x - self.left) // 2
        return row * self.cols + col

    def fill_empty_slots_with_random_colors(self) -> None:
        slots = self.cols * self.rows
        while len(self.colors) < slots:
            self.colors.append(Color.random())

    def render(self) -> None:
        super().render()
        colors = iter(self.colors)
        for y in range(self.top, self.bottom + 1):
            for x in range(self.left, self.right, 2):
                try:
                    color = next(colors)
                except StopIteration:
                    return
                draw(x, y, FILLED_PIXEL, color)

    def resize_up(self) -> None:
        if self.bottom > self.top:
            self.bottom -= 1

    def resize_down(self) -> None:
        self.bottom += 1
        self.fill_empty_slots_with_random_colors()

    def resize_left(self) -> None:
        if self.right > self.left + 2:
            self.right -= 2

    def resize_right(self) -> None:
        self.right += 2
        self.fill_empty_slots_with_random_colors()

    @property
    def rows(self) -> int:
        return self.bottom - self.top + 1

    @property
    def cols(self) -> int:
        return (self.right - self.left + 1) // 2

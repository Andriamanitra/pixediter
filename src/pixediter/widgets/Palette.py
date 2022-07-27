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
        self._color_from_coord: dict[tuple[int, int], Color] = {}
        self.colors: list[Color] = []
        self.set_colors(colors)
        self.selector = selector

    def onclick(self, ev: events.MouseEvent) -> bool:
        if ev.event_type != MouseEventType.MOUSE_DOWN:
            # this allows the default handler to run when the user starts drawing
            # a shape and then releases mouse above this widget, and when user
            # continues drawing over this widget when it's located on top of draw
            # area
            return False

        if ev.button in (MouseButton.LEFT, MouseButton.MIDDLE):
            color = self._color_from_coord.get((ev.x, ev.y), colors.WHITE)
            self.selector.set_color("primary", color)
            return True
        if ev.button == MouseButton.RIGHT:
            color = self._color_from_coord.get((ev.x, ev.y), colors.WHITE)
            self.selector.set_color("secondary", color)
            return True
        return False

    def move(self, dx: int, dy: int) -> None:
        super().move(dx, dy)
        self.set_colors(self.colors)

    def set_colors(self, colors: list[Color]) -> None:
        self._color_from_coord = {}
        self.colors = []
        color_index = 0
        for y in range(self.top, self.bottom + 1):
            for x in range(self.left, self.right, 2):
                if color_index >= len(colors):
                    new_color = Color.random()
                else:
                    new_color = colors[color_index]
                self.colors.append(new_color)
                self._color_from_coord[(x, y)] = new_color
                self._color_from_coord[(x + 1, y)] = new_color
                color_index += 1

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
        number_of_visible_colors = self.rows * self.cols
        extra_colors_needed = number_of_visible_colors - len(self.colors)
        extra_colors = [Color.random() for i in range(extra_colors_needed)]
        if extra_colors:
            self.set_colors(self.colors + extra_colors)

    def resize_left(self) -> None:
        if self.right > self.left + 2:
            self.right -= 2

    def resize_right(self) -> None:
        self.right += 2
        number_of_visible_colors = self.rows * self.cols
        extra_colors_needed = number_of_visible_colors - len(self.colors)
        extra_colors = [Color.random() for i in range(extra_colors_needed)]
        if extra_colors:
            self.set_colors(self.colors + extra_colors)

    @property
    def rows(self) -> int:
        return self.bottom - self.top + 1

    @property
    def cols(self) -> int:
        return (self.right - self.left + 1) // 2

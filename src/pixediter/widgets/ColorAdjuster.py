from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from pixediter import events
from pixediter.borders import Borders
from pixediter.colors import Color
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.utils import draw
from pixediter.utils import FILLED_PIXEL

from .TerminalWidget import TerminalWidget

if TYPE_CHECKING:
    from pixediter.application import App
    from pixediter.application import SelectedColors


class ColorAdjuster(TerminalWidget):
    def __init__(
            self,
            *,
            parent: App,
            top: int,
            left: int,
            borders: Optional[Borders] = None,
            color: SelectedColors
    ):
        self.width = 17
        super().__init__(
            parent=parent,
            bbox=(left, top, left + self.width - 1, top + 9),
            borders=borders
        )
        self.color = color
        self.delta = 0.1
        self._color_from_coord: dict[tuple[int, int], Color] = {}

    def onclick(self, ev: events.MouseEvent) -> bool:
        if ev.event_type == MouseEventType.MOUSE_UP:
            # this allows the default handler to run when the user starts drawing
            # a shape and then releases mouse above this widget
            return False

        if ev.button == MouseButton.SCROLL_UP:
            if self.delta > 0.005:
                self.delta -= 0.005
                self.render()
            return True
        if ev.button == MouseButton.SCROLL_DOWN:
            if self.delta < 0.20:
                self.delta += 0.005
                self.render()
            return True

        color = self._color_from_coord.get((ev.x, ev.y))
        if not color:
            return True
        if ev.button in (MouseButton.LEFT, MouseButton.MIDDLE):
            self.parent.set_color("primary", color)
        elif ev.button == MouseButton.RIGHT:
            self.parent.set_color("secondary", color)
        return True

    def render(self) -> None:
        def add_color(x: int, y: int, color: Color) -> None:
            self._color_from_coord[(x, y)] = color
            draw(x, y, FILLED_PIXEL[0], color)

        super().render()
        row = self.top
        draw(self.left, row, f"    {self.color.primary.hex()}" + " " * (self.width - 4 - 7))
        add_color(self.left + 1, row, self.color.primary)
        add_color(self.left + 2, row, self.color.primary)
        row += 1
        draw(self.left, row, f"    {self.color.secondary.hex()}" + " " * (self.width - 4 - 7))
        add_color(self.left + 1, row, self.color.secondary)
        add_color(self.left + 2, row, self.color.secondary)
        row += 1
        draw(self.left, row, " " * self.width)
        row += 1

        color = self.color.primary
        left = self.left + 1
        rgb_gradient_width = self.width - 4
        draw(left - 1, row + 0, "R")
        draw(left - 1, row + 1, "G")
        draw(left - 1, row + 2, "B")
        for i in range(rgb_gradient_width):
            rgb_delta = round(self.delta * 255 * (i - rgb_gradient_width // 2))
            r_adjusted = color.add_rgb(rgb_delta, 0, 0)
            g_adjusted = color.add_rgb(0, rgb_delta, 0)
            b_adjusted = color.add_rgb(0, 0, rgb_delta)
            add_color(left + i, row + 0, r_adjusted)
            add_color(left + i, row + 1, g_adjusted)
            add_color(left + i, row + 2, b_adjusted)
        draw(left + rgb_gradient_width, row + 0, f"{color.r:3}")
        draw(left + rgb_gradient_width, row + 1, f"{color.g:3}")
        draw(left + rgb_gradient_width, row + 2, f"{color.b:3}")
        row += 3
        draw(self.left, row, " " * self.width)
        row += 1

        hsl_gradient_width = self.width - 6
        draw(left - 1, row + 0, "H")
        draw(left - 1, row + 1, "S")
        draw(left - 1, row + 2, "L")
        for i in range(hsl_gradient_width):
            hsl_delta = self.delta * (i - hsl_gradient_width // 2)
            h_adjusted = color.add_hsl(hsl_delta, 0, 0)
            s_adjusted = color.add_hsl(0, hsl_delta, 0)
            l_adjusted = color.add_hsl(0, 0, hsl_delta)
            add_color(left + i, row + 0, h_adjusted)
            add_color(left + i, row + 1, s_adjusted)
            add_color(left + i, row + 2, l_adjusted)
        H, S, L = color.hsl()
        draw(left + hsl_gradient_width, row + 0, f"{H:.3f}")
        draw(left + hsl_gradient_width, row + 1, f"{S:.3f}")
        draw(left + hsl_gradient_width, row + 2, f"{L:.3f}")

    def resize_up(self) -> None:
        return

    def resize_down(self) -> None:
        return

    def resize_left(self) -> None:
        if self.width > 11:
            self.width -= 2
            self.right -= 2

    def resize_right(self) -> None:
        if self.width < 50:
            self.width += 2
            self.right += 2

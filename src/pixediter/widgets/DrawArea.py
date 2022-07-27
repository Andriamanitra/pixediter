from __future__ import annotations

from collections.abc import Callable
from typing import Optional

from pixediter import events
from pixediter.borders import Borders
from pixediter.colors import Color
from pixediter.ColorSelector import ColorSelector
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.image import ImageData
from pixediter.ToolSelector import ToolSelector
from pixediter.utils import draw
from pixediter.utils import FILLED_PIXEL
from pixediter.utils import rect

from .TerminalWidget import TerminalWidget


class DrawArea(TerminalWidget):
    def __init__(
            self,
            *,
            bbox: tuple[int, int, int, int],
            borders: Optional[Borders] = None,
            image: ImageData,
            color: ColorSelector,
            tools: ToolSelector,
            full_app_redraw: Callable[[], None]
    ):
        super().__init__(bbox=bbox, borders=borders)
        self.image = image
        self.starting_pos: Optional[tuple[int, int]] = None
        self._prev_pos = (-1, -1)
        self.color = color
        self.tools = tools
        self.full_app_redraw = full_app_redraw

    def onclick(self, ev: events.MouseEvent) -> bool:
        img_x, img_y = self.terminal_coords_to_img_coords(ev.x, ev.y)

        if ev.button in (MouseButton.RIGHT, MouseButton.RIGHT_DRAG):
            color = self.color.secondary
        else:
            color = self.color.primary

        match self.tools.current, ev.event_type, ev.button:
            case _, MouseEventType.MOUSE_DOWN | MouseEventType.MOUSE_DRAG, MouseButton.MIDDLE:
                self.color.set_color("primary", self.image[img_x, img_y])

            case "Pencil", MouseEventType.MOUSE_DOWN | MouseEventType.MOUSE_DRAG, MouseButton.LEFT | MouseButton.RIGHT:
                self.paint(img_x, img_y, color)

            case "Rectangle", MouseEventType.MOUSE_DOWN, MouseButton.LEFT | MouseButton.RIGHT:
                self.starting_pos = (img_x, img_y)
                self._prev_pos = (img_x, img_y)

            case "Rectangle", MouseEventType.MOUSE_DRAG, MouseButton.LEFT | MouseButton.RIGHT:
                if self.starting_pos is None:
                    return False

                drawn = set()
                # draw current
                start_x, start_y = self.starting_pos
                for x, y in rect(start_x, start_y, img_x, img_y):
                    self.render_pixel(x, y, color)
                    drawn.add((x, y))

                # clean up previous
                for x, y in rect(*self.starting_pos, *self._prev_pos):
                    if (x, y) not in drawn:
                        self.render_pixel(x, y, self.image[x, y])

                self._prev_pos = (img_x, img_y)

            case "Rectangle", MouseEventType.MOUSE_UP, MouseButton.LEFT | MouseButton.RIGHT:
                if self.starting_pos is None:
                    return False
                self.image.paint_rectangle(*self.starting_pos, img_x, img_y, color)
                self.starting_pos = None
                self.full_app_redraw()

            case "Fill", MouseEventType.MOUSE_DOWN, MouseButton.LEFT | MouseButton.RIGHT:
                from_color = self.image[img_x, img_y]
                if from_color == color:
                    return True
                width = self.image.width
                height = self.image.height
                stack = [(img_x, img_y)]
                visited = set()
                while stack:
                    x, y = xy = stack.pop()
                    if self.image[x, y] != from_color:
                        continue
                    self.paint(x, y, color)
                    visited.add(xy)
                    if y > 0 and (x, y - 1) not in visited:
                        stack.append((x, y - 1))
                    if x > 0 and (x - 1, y) not in visited:
                        stack.append((x - 1, y))
                    if y < height - 1 and (x, y + 1) not in visited:
                        stack.append((x, y + 1))
                    if x < width - 1 and (x + 1, y) not in visited:
                        stack.append((x + 1, y))

            case _, MouseEventType.MOUSE_UP, MouseButton.LEFT | MouseButton.RIGHT:
                self.full_app_redraw()

            case _:
                return False

        return True

    def render(self) -> None:
        super().render()
        for (x, y), color in self.image:
            self.render_pixel(x, y, color)

    def terminal_coords_to_img_coords(self, x: int, y: int) -> tuple[int, int]:
        img_x = (x - self.left) // 2
        img_y = y - self.top
        return img_x, img_y

    def paint(self, img_x: int, img_y: int, color: Color) -> None:
        self.image[img_x, img_y] = color
        self.render_pixel(img_x, img_y, color)

    def render_pixel(self, x: int, y: int, color: Color) -> None:
        # pixels are 2 characters wide
        x = self.left + 2 * x
        y = self.top + y
        draw(x, y, FILLED_PIXEL, color)

    def set_image(self, image: ImageData) -> None:
        self.image = image
        self._update_pos()

    def crop(self, x0: int, y0: int, x1: int, y1: int) -> None:
        self.image.crop(x0, y0, x1, y1)
        self._update_pos()

    def _update_pos(self) -> None:
        self.right = self.left + 2 * self.image.width - 1
        self.bottom = self.top + self.image.height - 1

    def resize_up(self) -> None:
        if self.image.height > 1:
            self.crop(0, 0, self.image.width, self.image.height - 1)

    def resize_down(self) -> None:
        self.crop(0, 0, self.image.width, self.image.height + 1)

    def resize_left(self) -> None:
        if self.image.width > 1:
            self.crop(0, 0, self.image.width - 1, self.image.height)

    def resize_right(self) -> None:
        self.crop(0, 0, self.image.width + 1, self.image.height)

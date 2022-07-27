from __future__ import annotations

from typing import Optional

from pixediter import events
from pixediter.borders import Borders
from pixediter.colors import Color
from pixediter.ColorSelector import ColorSelector
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.image import ImageData
from pixediter.tools import DrawEvent
from pixediter.ToolSelector import ToolSelector
from pixediter.utils import draw
from pixediter.utils import FILLED_PIXEL

from .TerminalWidget import TerminalWidget


class DrawArea(TerminalWidget):
    def __init__(
            self,
            *,
            bbox: tuple[int, int, int, int],
            borders: Optional[Borders] = None,
            image: ImageData,
            color: ColorSelector,
            tools: ToolSelector
    ):
        super().__init__(bbox=bbox, borders=borders)
        self.image = image
        self.color = color
        self.tools = tools

    def onclick(self, ev: events.MouseEvent) -> bool:
        img_x, img_y = self.terminal_coords_to_img_coords(ev.x, ev.y)
        draw_event = DrawEvent((img_x, img_y), ev.event_type, ev.button, self.color)

        if ev.event_type == MouseEventType.MOUSE_DOWN:
            handled = self.tools.current.mouse_down(self.image, draw_event, self.render_pixel)
        elif ev.event_type == MouseEventType.MOUSE_DRAG:
            handled = self.tools.current.mouse_drag(self.image, draw_event, self.render_pixel)
        elif ev.event_type == MouseEventType.MOUSE_UP:
            handled = self.tools.current.mouse_up(self.image, draw_event, self.render_pixel)

        if handled:
            return True

        if ev.event_type in (MouseEventType.MOUSE_DOWN, MouseEventType.MOUSE_DRAG) and ev.button == MouseButton.MIDDLE:
            self.color.set_color("primary", self.image[img_x, img_y])
            return True

        return False

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

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from pixediter.colors import Color
from pixediter.ColorSelector import ColorSelector
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.image import ImageData
from pixediter.utils import rect


DrawFn = Callable[[int, int, Color], None]


@dataclass
class DrawEvent:
    pos: tuple[int, int]
    type: MouseEventType
    button: MouseButton
    color: ColorSelector

    def active_color(self) -> Color:
        if self.button == MouseButton.RIGHT:
            return self.color.secondary
        return self.color.primary


class Tool(Protocol):
    def mouse_down(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        ...

    def mouse_up(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        ...

    def mouse_drag(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        ...

    def reset_state(self) -> None:
        ...

    @property
    def name(self) -> str:
        ...


class PencilTool:
    name = "Pencil"

    @staticmethod
    def mouse_down(img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        return PencilTool.mouse_drag(img, ev, draw)

    @staticmethod
    def mouse_up(img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        return False

    @staticmethod
    def mouse_drag(img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if ev.button in (MouseButton.LEFT, MouseButton.RIGHT):
            color = ev.active_color()
            draw(*ev.pos, color)
            img[ev.pos] = color
            return True
        return False

    @staticmethod
    def reset_state() -> None:
        pass


class RectangleTool:
    name = "Rectangle"

    def __init__(self) -> None:
        self.starting_pos = (-1, -1)
        self.previous_pos = (-1, -1)

    def is_started(self) -> bool:
        return self.starting_pos != (-1, -1)

    def mouse_down(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if self.is_started():
            # pressing another mouse button while previewing (dragging) cancels the draw
            self.reset_state()
            return True
        if ev.button in (MouseButton.LEFT, MouseButton.RIGHT):
            self.starting_pos = ev.pos
            self.previous_pos = ev.pos
            draw(*ev.pos, ev.active_color())
            return True

        return False

    def mouse_drag(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if not self.is_started():
            return False
        color = ev.active_color()
        start_x, start_y = self.starting_pos
        curr_x, curr_y = ev.pos
        prev_x, prev_y = self.previous_pos

        drawn = set()
        # draw current
        for x, y in rect(start_x, start_y, curr_x, curr_y):
            draw(x, y, color)
            drawn.add((x, y))

        # clean up previous
        for x, y in rect(start_x, start_y, prev_x, prev_y):
            if (x, y) not in drawn:
                draw(x, y, img[x, y])

        self.previous_pos = ev.pos
        return True

    def mouse_up(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if not self.is_started():
            return False

        # draw permanently
        color = ev.active_color()
        start_x, start_y = self.starting_pos
        curr_x, curr_y = ev.pos
        for x, y in rect(start_x, start_y, curr_x, curr_y):
            img[x, y] = color
        return True

    def reset_state(self) -> None:
        self.previous_pos = (-1, -1)
        self.starting_pos = (-1, -1)


class LineTool:
    name = "Line"

    def __init__(self) -> None:
        self.starting_pos = (-1, -1)
        self.previous_pos = (-1, -1)

    def is_started(self) -> bool:
        return self.starting_pos != (-1, -1)

    def line(self, from_pos: tuple[int, int], to_pos: tuple[int, int]) -> Iterator[tuple[int, int]]:
        x0, y0 = from_pos
        x1, y1 = to_pos

        if x0 == x1:
            if y1 < y0:
                y0, y1 = y1, y0
            for y in range(y0, y1 + 1):
                yield x0, y
            return
        if y0 == y1:
            if x1 < x0:
                x0, x1 = x1, x0
            for x in range(x0, x1 + 1):
                yield x, y0
            return

        x_change = x1 - x0
        y_change = y1 - y0

        # iterate over whichever of horizontal/vertical has the larger change and only place one
        # pixel per coordinate on that axis to make a thin line
        if abs(x_change) > abs(y_change):
            sign = 1 if x_change > 0 else -1
            for x in range(0, x_change + sign, sign):
                y = round(x / x_change * y_change)
                yield x0 + x, y0 + y
        else:
            sign = 1 if y_change > 0 else -1
            for y in range(0, y_change + sign, sign):
                x = round(y / y_change * x_change)
                yield x0 + x, y0 + y

    def mouse_down(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if self.is_started():
            # pressing another mouse button while previewing (dragging) cancels the draw
            self.reset_state()
            return True
        if ev.button in (MouseButton.LEFT, MouseButton.RIGHT):
            self.starting_pos = ev.pos
            self.previous_pos = ev.pos
            draw(*ev.pos, ev.active_color())
            return True

        return False

    def mouse_drag(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if not self.is_started():
            return False
        color = ev.active_color()

        drawn = set()
        # draw current
        for x, y in self.line(self.starting_pos, ev.pos):
            draw(x, y, color)
            drawn.add((x, y))

        # clean up previous
        for x, y in self.line(self.starting_pos, self.previous_pos):
            if (x, y) not in drawn:
                draw(x, y, img[x, y])

        self.previous_pos = ev.pos
        return True

    def mouse_up(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if not self.is_started():
            return False

        # draw permanently
        color = ev.active_color()
        for x, y in self.line(self.starting_pos, ev.pos):
            img[x, y] = color
        return True

    def reset_state(self) -> None:
        self.previous_pos = (-1, -1)
        self.starting_pos = (-1, -1)


class FillTool:
    name = "Fill"

    def mouse_down(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        img_x, img_y = ev.pos
        from_color = img[img_x, img_y]
        color = ev.active_color()
        if from_color == color:
            return True
        stack = [(img_x, img_y)]
        visited = set()
        while stack:
            x, y = xy = stack.pop()
            if img[x, y] != from_color:
                continue
            draw(x, y, color)
            img[x, y] = color
            visited.add(xy)
            if y > 0 and (x, y - 1) not in visited:
                stack.append((x, y - 1))
            if x > 0 and (x - 1, y) not in visited:
                stack.append((x - 1, y))
            if y < img.height - 1 and (x, y + 1) not in visited:
                stack.append((x, y + 1))
            if x < img.width - 1 and (x + 1, y) not in visited:
                stack.append((x + 1, y))
        return True

    def mouse_up(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        return False

    def mouse_drag(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        return self.mouse_down(img, ev, draw)

    def reset_state(self) -> None:
        pass

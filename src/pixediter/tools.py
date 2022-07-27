from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from pixediter.colors import Color
from pixediter.ColorSelector import ColorSelector
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.image import ImageData
from pixediter.utils import rect


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


DrawFn = Callable[[int, int, Color], None]


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

    def mouse_up(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if not self.is_started():
            return False

        color = ev.active_color()
        start_x, start_y = self.starting_pos
        curr_x, curr_y = ev.pos
        prev_x, prev_y = self.previous_pos
        if ev.button in (MouseButton.LEFT, MouseButton.RIGHT):
            drawn = set()
            # draw current
            for x, y in rect(start_x, start_y, curr_x, curr_y):
                draw(x, y, color)
                img[x, y] = color
                drawn.add((x, y))

            # clean up previous
            for x, y in rect(start_x, start_y, prev_x, prev_y):
                if (x, y) not in drawn:
                    draw(x, y, img[x, y])
            self.starting_pos = (-1, -1)
        return True

    def mouse_down(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
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


my_tools: list[Tool] = [PencilTool(), RectangleTool(), FillTool()]

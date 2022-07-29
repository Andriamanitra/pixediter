from __future__ import annotations

import math
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
Pos = tuple[int, int]


@dataclass
class DrawEvent:
    pos: Pos
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

    def line(self, from_pos: Pos, to_pos: Pos) -> Iterator[Pos]:
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


def vector_projection(target: Pos, vec: Pos) -> tuple[float, float]:
    """Returns component of vec that is parallel to target"""
    target_x, target_y = target
    vec_x, vec_y = vec
    dot = target_x * vec_x + target_y * vec_y
    abs_target_squared = target_x ** 2 + target_y ** 2
    multiplier = dot / abs_target_squared
    return (multiplier * target_x, multiplier * target_y)


class Gradient:
    name = "Gradient"

    def __init__(self) -> None:
        self.start = (-1, -1)
        self.color_a = Color(0, 0, 0)
        self.color_b = Color(255, 255, 255)
        self.last_drawn: dict[Pos, Color] = {}

    @staticmethod
    def radial_gradient(
            img: ImageData,
            center: Pos,
            end: Pos,
            color_a: Color,
            color_b: Color,
            lerp_fn: Callable[[Color, Color, float], Color] = Color.lerp_rgb
    ) -> Iterator[tuple[Pos, Color]]:
        if center == end:
            yield center, color_a
            return
        cx, cy = center
        ex, ey = end
        radius = math.hypot(ex - cx, ey - cy)
        x0 = max(0, math.floor(cx - radius))
        x1 = min(img.width, math.ceil(cx + radius + 1))
        y0 = max(0, math.floor(cy - radius))
        y1 = min(img.height, math.ceil(cy + radius + 1))
        for x in range(x0, x1):
            for y in range(y0, y1):
                dist_from_center = math.hypot(x - cx, y - cy)
                if dist_from_center <= radius:
                    color = lerp_fn(color_a, color_b, dist_from_center / radius)
                    yield (x, y), color

    @staticmethod
    def linear_gradient(
            img: ImageData,
            start: Pos,
            end: Pos,
            color_a: Color,
            color_b: Color,
            lerp_fn: Callable[[Color, Color, float], Color] = Color.lerp_rgb
    ) -> Iterator[tuple[Pos, Color]]:
        if start == end:
            yield start, color_a
            return
        ax, ay = start
        bx, by = end
        a_to_b = (ab_x, ab_y) = (bx - ax, by - ay)
        for (x, y), _color in img:
            a_to_c = (x - ax, y - ay)
            proj_x, proj_y = vector_projection(a_to_b, a_to_c)
            # opposite direction => before the starting point => ignore
            if (proj_x * ab_x < 0) or (proj_y * ab_y < 0):
                continue
            # longer than a_to_b => after the end point => ignore
            elif abs(proj_x) > abs(ab_x) or abs(proj_y) > abs(ab_y):
                continue
            else:
                # between a and b => interpolate a color
                val = (proj_x ** 2 + proj_y ** 2) ** 0.5 / (ab_x ** 2 + ab_y ** 2) ** 0.5
                color = lerp_fn(color_a, color_b, val)
                yield (x, y), color

    def is_started(self) -> bool:
        return self.start != (-1, -1)

    def mouse_down(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if self.is_started():
            # pressing another mouse button while previewing (dragging) cancels the draw
            self.reset_state()
            return True

        if ev.button.left():
            self.color_a = ev.color.primary
            self.color_b = ev.color.secondary
        elif ev.button.right():
            self.color_a = ev.color.secondary
            self.color_b = ev.color.primary
        else:
            return False

        x, y = ev.pos
        draw(x, y, self.color_a)
        self.last_drawn = {ev.pos: self.color_a}
        self.start = ev.pos
        return True

    def mouse_up(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if not self.is_started():
            return False
        for (x, y), color in self.last_drawn.items():
            img[x, y] = color
        self.reset_state()
        return True

    def mouse_drag(self, img: ImageData, ev: DrawEvent, draw: DrawFn) -> bool:
        if not self.is_started():
            return False
        if self.start == ev.pos:
            return True
        drawn = {}
        lerp = Color.lerp_hsl if ev.button.alt() else Color.lerp_rgb
        gradient = self.radial_gradient if ev.button.ctrl() else self.linear_gradient
        for (x, y), color in gradient(img, self.start, ev.pos, self.color_a, self.color_b, lerp):
            drawn[x, y] = color
            draw(x, y, color)
        for x, y in self.last_drawn:
            if (x, y) not in drawn:
                draw(x, y, img[x, y])
        self.last_drawn = drawn
        return True

    def reset_state(self) -> None:
        self.start = (-1, -1)
        self.last_drawn = {}

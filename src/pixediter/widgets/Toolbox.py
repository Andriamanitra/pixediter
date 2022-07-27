from __future__ import annotations

from typing import Optional

from pixediter import colors
from pixediter import events
from pixediter.borders import Borders
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.ToolSelector import ToolSelector
from pixediter.utils import draw

from .TerminalWidget import TerminalWidget


class Toolbox(TerminalWidget):
    def __init__(
            self,
            *,
            top: int,
            left: int,
            width: Optional[int] = None,
            borders: Optional[Borders] = None,
            selector: ToolSelector
    ):
        if width is None:
            width = max(len(tool.name) for tool in selector)
        right = left + width - 1
        bottom = top + len(selector) - 1
        bbox = (left, top, right, bottom)
        super().__init__(bbox=bbox, borders=borders)
        self.width = width
        self.selector = selector

    def onclick(self, ev: events.MouseEvent) -> bool:
        if ev.event_type == MouseEventType.MOUSE_DOWN and ev.button == MouseButton.LEFT:
            tool_index = ev.y - self.top
            self.selector.select_by_index(tool_index)
            self.render()
            return True
        return False

    def render(self) -> None:
        super().render()
        y = self.top
        for tool in self.selector:
            color = colors.WHITE if tool == self.selector.current else colors.GRAY
            toolstr = tool.name.ljust(self.width)[:self.width]
            draw(self.left, y, toolstr, color=color)
            y += 1

    def resize_left(self) -> None:
        if self.right > self.left + 1:
            self.width -= 1
            self.right -= 1

    def resize_right(self) -> None:
        self.width += 1
        self.right += 1

    def resize_up(self) -> None:
        return

    def resize_down(self) -> None:
        return

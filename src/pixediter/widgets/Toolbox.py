from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from pixediter import colors
from pixediter import events
from pixediter.borders import Borders
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.utils import draw

from .TerminalWidget import TerminalWidget

if TYPE_CHECKING:
    from pixediter.application import App


class Toolbox(TerminalWidget):
    def __init__(
            self,
            *,
            parent: App,
            top: int,
            left: int,
            width: Optional[int] = None,
            borders: Optional[Borders] = None,
            tools: list[str]
    ):
        if width is None:
            width = max(len(tool) for tool in tools)
        right = left + width - 1
        bottom = top + len(tools) - 1
        bbox = (left, top, right, bottom)
        super().__init__(parent=parent, bbox=bbox, borders=borders)
        self.width = width
        self.tools = tools

    def onclick(self, ev: events.MouseEvent) -> bool:
        if ev.event_type == MouseEventType.MOUSE_DOWN and ev.button == MouseButton.LEFT:
            tool_index = ev.y - self.top
            self.parent.tool = self.tools[tool_index]
            self.render()
            return True
        return False

    def render(self) -> None:
        super().render()
        y = self.top
        for tool in self.tools:
            color = colors.WHITE if tool == self.parent.tool else colors.GRAY
            toolstr = tool.ljust(self.width)[:self.width]
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

from __future__ import annotations

import os
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from typing import NoReturn

import pixediter
from pixediter import borders
from pixediter import colors
from pixediter import events
from pixediter import terminal
from pixediter import tools
from pixediter.ColorSelector import ColorSelector
from pixediter.events import MouseEvent
from pixediter.events import MouseEventType
from pixediter.image import ImageData
from pixediter.ToolSelector import ToolSelector
from pixediter.utils import draw
from pixediter.widgets.ColorAdjuster import ColorAdjuster
from pixediter.widgets.DrawArea import DrawArea
from pixediter.widgets.Palette import Palette
from pixediter.widgets.TerminalWidget import TerminalWidget
from pixediter.widgets.Toolbox import Toolbox

TITLE = f"PixEdiTer v{pixediter.__version__}"
debugging = "DEBUG" in os.environ


class App:
    def __init__(self, width: int = 16, height: int = 16):
        self.MARGIN_LEFT = 3

        self.color = ColorSelector(primary=colors.GRAY, secondary=colors.WHITE)
        self.tool = ToolSelector(tools.PencilTool(), tools.RectangleTool(), tools.FillTool())

        DRAW_AREA_LEFT = self.MARGIN_LEFT
        DRAW_AREA_TOP = 3
        DRAW_AREA_RIGHT = DRAW_AREA_LEFT + 2 * width - 1
        DRAW_AREA_BOTTOM = DRAW_AREA_TOP + height - 1

        self.terminal_columns, self.terminal_rows = terminal.size()

        self.draw_area = DrawArea(
            bbox=(DRAW_AREA_LEFT, DRAW_AREA_TOP, DRAW_AREA_RIGHT, DRAW_AREA_BOTTOM),
            borders=borders.sharp,
            image=ImageData(width, height),
            color=self.color,
            tools=self.tool
        )

        palette_top = DRAW_AREA_BOTTOM + 3
        self.palette = Palette(
            bbox=(DRAW_AREA_LEFT, palette_top, DRAW_AREA_LEFT + 31, palette_top + 1),
            borders=borders.sharp,
            colors=Palette.default_colors,
            selector=self.color
        )

        self.toolbox = Toolbox(
            top=DRAW_AREA_TOP,
            left=DRAW_AREA_RIGHT + 4,
            width=10,
            borders=borders.sharp,
            selector=self.tool
        )

        self.color_adjuster = ColorAdjuster(
            top=self.toolbox.bottom + 3,
            left=DRAW_AREA_RIGHT + 4,
            borders=borders.sharp,
            color=self.color
        )

        self.widgets = [
            self.draw_area,
            self.palette,
            self.toolbox,
            self.color_adjuster
        ]
        for i, widget in enumerate(self.widgets):
            widget.title = str(i)

        self.commands: dict[str, Callable[[str, list[str]], Any]] = {
            ":help": self.show_help,
            ":h": self.show_help,
            ":?": self.show_help,
            ":q": self.exit,
            ":quit": self.exit,
            ":new": self.new_image,
            ":open": self.load_image_cmd,
            ":save": self.save_image_cmd,
            ":crop": self.crop,
        }

        self._waiting_for_key = False
        self.full_redraw()

    def exit(self, *args: Any) -> NoReturn:
        """exits the program without saving"""
        terminal.clear()
        raise SystemExit(0)

    def draw_title(self) -> None:
        draw(4, 1, TITLE, colors.GREEN)

    def full_redraw(self) -> None:
        terminal.clear()
        self.terminal_columns, self.terminal_rows = terminal.size()
        self.draw_title()
        for widget in self.widgets:
            widget.render()

    def new_image(self, cmd: str, args: list[str]) -> None:
        """
        :new <width: int> <height: int> -- replaces canvas with a new image
        """
        width, height = map(int, args)
        self.draw_area.set_image(ImageData(width, height))
        self.full_redraw()

    def crop(self, cmd: str, args: list[str]) -> None:
        """
        :crop <x0: int> <y0: int> <x1: int> <y1: int> -- crops image to area between given coordinates
        """
        if len(args) == 2:
            x0, y0, x1, y1 = 0, 0, int(args[0]), int(args[1])
        elif len(args) == 4:
            x0, y0, x1, y1 = [int(arg) for arg in args]
        else:
            raise ValueError("crop requires exactly 2 or 4 arguments")
        self.draw_area.crop(x0, y0, x1, y1)
        self.full_redraw()

    def debug(self, to_show: str) -> None:
        if debugging:
            self.show(to_show)

    def show(self, to_show: Any) -> None:
        available_space = self.terminal_columns - self.MARGIN_LEFT
        padded_text = str(to_show).ljust(available_space)[:available_space]
        draw(self.MARGIN_LEFT, self.terminal_rows - 1, padded_text)

    def unknown_command(self, cmd: str, args: list[str]) -> None:
        self.show(f"Unknown command '{cmd}'")

    def set_image_file_path(self, file_path: str) -> None:
        self.draw_area.image.filepath = file_path

    def load_image(self, file_path: str) -> None:
        image = ImageData.from_file(file_path)
        self.draw_area.set_image(image)
        self.full_redraw()

    def load_image_cmd(self, cmd: str, args: list[str]) -> None:
        """
        :open <path: str> -- opens an image from <path> (requires Pillow)
        """
        file_path, = args
        self.load_image(file_path)

    def save_image_cmd(self, cmd: str, args: list[str]) -> None:
        """
        :save [<path: str>] -- saves the image into <path> (requires Pillow)
        """
        if not args:
            filepath = None
        else:
            filepath, = args
        self.draw_area.image.save_file(filepath)
        self.show(f"Saved image as {self.draw_area.image.filepath}")

    def show_help(self, cmd: str, args: list[str]) -> None:
        """
        shows keybindings and commands
        """
        terminal.clear()
        self.draw_title()
        row_number = 3
        # TODO: support customizable bindings
        draw(self.MARGIN_LEFT, row_number, "Keybindings:", colors.GREEN)
        row_number += 1
        keybindings = {
            "middle click": "pick A color",
            "ctrl-s": "save",
            ":  OR  ctrl-e": "open command line",
            "r": "force redraw",
            "q": "exit without saving",
            "?": "show this help"
        }
        for key, action in keybindings.items():
            draw(self.MARGIN_LEFT + 2, row_number, key, colors.WHITE)
            draw(self.MARGIN_LEFT + 4, row_number + 1, action, colors.GRAY)
            row_number += 2

        row_number += 1
        draw(self.MARGIN_LEFT, row_number, "Commands:", colors.GREEN)
        already_shown = set()
        row_number += 1
        for cmd, func in self.commands.items():
            if func in already_shown:
                continue
            explanation = str(func.__doc__).strip().split("\n")[0]
            draw(self.MARGIN_LEFT + 2, row_number, cmd)
            draw(self.MARGIN_LEFT + 4, row_number + 1, explanation, colors.GRAY)
            already_shown.add(func)
            row_number += 2

        draw(self.MARGIN_LEFT, row_number + 2, "Press any key to continue...")
        self._waiting_for_key = True

    def selected_widgets(self) -> Generator[TerminalWidget, None, None]:
        for widget in self.widgets:
            if widget.selected:
                yield widget

    @contextmanager
    def handled_exceptions(self, *exception_types: type) -> Iterator[None]:
        try:
            yield
        except Exception as exc:
            if any(isinstance(exc, exc_type) for exc_type in exception_types):
                self.show(f"Error: {exc}")
            else:
                raise

    def run(self) -> None:
        cmd = ""
        for ev in events.listen():
            if self._waiting_for_key:
                self.full_redraw()
                self._waiting_for_key = False
                continue

            if isinstance(ev, MouseEvent):
                self._handle_click(ev)
                continue

            if cmd:
                if ev == "backspace":
                    cmd = cmd[:-1]
                    self.show(cmd)
                elif ev == "\n":
                    cmd, *args = cmd.split()
                    with self.handled_exceptions(Exception):
                        self.commands.get(cmd, self.unknown_command)(cmd, args)
                    cmd = ""
                elif not isinstance(ev, MouseEvent) and len(ev) == 1:
                    cmd += ev
                    self.show(cmd)
                continue

            if ev in {"q", "ctrl-q"}:
                self.exit()
            elif ev in {":", "ctrl-e"}:
                cmd = ":"
                self.show(cmd)
            elif ev == "?":
                self.commands[":help"](":help", [])
            elif ev == "r":
                self.full_redraw()
            elif ev in set("0123456789"):
                i = int(ev)
                if i < len(self.widgets):
                    self.widgets[i].toggle_selected()
                    self.full_redraw()
            elif ev == "up":
                for widget in self.selected_widgets():
                    widget.move(0, -1)
                self.full_redraw()
            elif ev == "down":
                for widget in self.selected_widgets():
                    widget.move(0, 1)
                self.full_redraw()
            elif ev == "left":
                for widget in self.selected_widgets():
                    widget.move(-1, 0)
                self.full_redraw()
            elif ev == "right":
                for widget in self.selected_widgets():
                    widget.move(1, 0)
                self.full_redraw()
            elif ev == "ctrl-up":
                for widget in self.selected_widgets():
                    widget.resize_up()
                self.full_redraw()
            elif ev == "ctrl-down":
                for widget in self.selected_widgets():
                    widget.resize_down()
                self.full_redraw()
            elif ev == "ctrl-left":
                for widget in self.selected_widgets():
                    widget.resize_left()
                self.full_redraw()
            elif ev == "ctrl-right":
                for widget in self.selected_widgets():
                    widget.resize_right()
                self.full_redraw()
            elif ev == "ctrl-s":
                with self.handled_exceptions(Exception):
                    self.commands[":save"](":save", [])
            else:
                self.debug(f"got event: {ev!r}")

    def _handle_click(self, ev: MouseEvent) -> None:
        for widget in reversed(self.widgets):
            if widget.contains(ev.x, ev.y):
                handled = widget.onclick(ev)
                if handled:
                    break
        if ev.event_type == MouseEventType.MOUSE_UP:
            # this needs to be handled here rather than in tools themselves because MOUSE_UP
            # event may happen outside DrawArea widget
            self.tool.current.reset_state()
            # some of the drawing may have happened on top of widgets
            # that had been moved to on top of DrawArea
            for widget in self.widgets:
                widget.render()
        self.debug(f"got event: {ev!r}")

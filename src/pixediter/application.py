import pixediter
from pixediter import borders
from pixediter import colors
from pixediter import events
from pixediter import terminal
from pixediter.colors import Color
from pixediter.events import MouseEventType
from pixediter.utils import draw
from pixediter.widgets import DrawArea
from pixediter.widgets import Palette
from pixediter.widgets import Toolbox

TITLE = f"PixEdiTer v{pixediter.__version__}"


class ImageData:
    def __init__(self, width=16, height=16, filepath=None):
        self.width = width
        self.height = height
        self.filepath = filepath
        self.pixels = [[colors.WHITE for w in range(width)] for h in range(height)]

    @classmethod
    def from_file(cls, filepath: str):
        from PIL import Image
        with Image.open(filepath) as image:
            width, height = image.size
            new = cls(width, height, filepath)
            for x in range(width):
                for y in range(height):
                    r, g, b = image.getpixel((x, y))
                    new[x, y] = Color(r, g, b)
        return new

    def save_file(self, filepath=None):
        if filepath is None:
            if self.filepath is None:
                raise Exception("Cannot save: file path not given")
            filepath = self.filepath

        from PIL import Image
        image = Image.new("RGB", (self.width, self.height))
        for x in range(self.width):
            for y in range(self.height):
                image.putpixel((x, y), self[x, y].rgb())
        image.save(filepath)
        self.filepath = filepath

    def crop(self, x0, y0, x1, y1):
        new_pixels = []
        if x1 < x0:
            x0, x1, = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0

        for y in range(y0, y1):
            row = []
            for x in range(x0, x1):
                if 0 <= y < self.height and 0 <= x < self.width:
                    pixel = self[x, y]
                else:
                    pixel = colors.WHITE
                row.append(pixel)
            new_pixels.append(row)
        self.height = len(new_pixels)
        self.width = len(new_pixels[0])
        self.pixels = new_pixels

    def paint_rectangle(self, x0, y0, x1, y1, color):
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        for x in range(x0, x1 + 1):
            self.pixels[y0][x] = color
            self.pixels[y1][x] = color
        for y in range(y0, y1 + 1):
            self.pixels[y][x0] = color
            self.pixels[y][x1] = color

    def __iter__(self):
        for row_index, row in enumerate(self.pixels):
            for col_index, pixel in enumerate(row):
                yield (col_index, row_index), pixel

    def __getitem__(self, xy: tuple[int, int]):
        x, y = xy
        return self.pixels[y][x]

    def __setitem__(self, xy: tuple[int, int], color) -> None:
        x, y = xy
        self.pixels[y][x] = color


class App:
    def __init__(self, width=16, height=16):
        self.MARGIN_LEFT = 3

        DRAW_AREA_LEFT = self.MARGIN_LEFT
        DRAW_AREA_TOP = 3
        DRAW_AREA_RIGHT = DRAW_AREA_LEFT + 2 * width - 1
        DRAW_AREA_BOTTOM = DRAW_AREA_TOP + height - 1

        self.draw_area = DrawArea(
            parent=self,
            bbox=(DRAW_AREA_LEFT, DRAW_AREA_TOP, DRAW_AREA_RIGHT, DRAW_AREA_BOTTOM),
            borders=borders.sharp,
            image=ImageData(width, height)
        )

        self.terminal_columns, self.terminal_rows = terminal.size()

        PALETTE_LEFT = self.MARGIN_LEFT
        PALETTE_TOP = DRAW_AREA_BOTTOM + 3
        PALETTE_RIGHT = self.MARGIN_LEFT + 32 - 1
        PALETTE_BOTTOM = PALETTE_TOP + 1
        self.palette = Palette(
            parent=self,
            bbox=(PALETTE_LEFT, PALETTE_TOP, PALETTE_RIGHT, PALETTE_BOTTOM),
            borders=borders.sharp,
            colors=Palette.default_colors
        )
        self.color = colors.BLACK
        self.secondary_color = colors.WHITE

        self.toolbox = Toolbox(
            parent=self,
            top=DRAW_AREA_TOP,
            left=DRAW_AREA_RIGHT + 4,
            width=10,
            borders=borders.sharp,
            tools=[
                "Pencil",
                "Rectangle",
                "Fill",
            ]
        )
        self.tool = "Pencil"

        self.widgets = [
            self.draw_area,
            self.palette,
            self.toolbox
        ]
        for i, widget in enumerate(self.widgets):
            widget.title = str(i)

        self.commands = {
            ":help": self.show_help,
            ":h": self.show_help,
            ":?": self.show_help,
            ":q": self.exit,
            ":quit": self.exit,
            ":new": self.new_image,
            ":open": self.load_file,
            ":save": self.save_file,
            ":crop": self.crop,
        }

        self._needs_redraw = False
        self.full_redraw()

    def exit(self, *args):
        """exits the program without saving"""
        terminal.clear()
        raise SystemExit(0)

    def draw_title(self):
        draw(4, 1, TITLE, colors.GREEN)

    def full_redraw(self):
        terminal.clear()
        self.terminal_columns, self.terminal_rows = terminal.size()
        self.draw_title()
        for widget in self.widgets:
            widget.render()

    def new_image(self, cmd, args):
        """
        :new <width: int> <height: int> -- replaces canvas with a new image
        """
        width, height = args
        width = int(width)
        height = int(height)
        self.draw_area.set_image(ImageData(width, height))
        self.full_redraw()

    def crop(self, cmd, args):
        """
        :crop <x0: int> <y0: int> <x1: int> <y1: int> -- crops image to area between given coordinates
        """
        if len(args) == 2:
            x0, y0, x1, y1 = 0, 0, int(args[0]), int(args[1])
        elif len(args) == 4:
            x0, y0, x1, y1 = [int(arg) for arg in args]
        else:
            raise ValueError("crop requires exactly 2 or 4 arguments")
        try:
            self.draw_area.crop(x0, y0, x1, y1)
        except Exception as exc:
            self.show(exc)
        else:
            self.full_redraw()

    def set_primary_color(self, color):
        self.color = color
        self.show(f"Primary color: {self.color} – hex: {self.color.hex()}")

    def set_secondary_color(self, color):
        self.secondary_color = color
        self.show(f"Secondary color: {self.secondary_color} – hex: {self.secondary_color.hex()}")

    def show(self, to_show):
        available_space = self.terminal_columns - self.MARGIN_LEFT
        padded_text = str(to_show).ljust(available_space)[:available_space]
        draw(self.MARGIN_LEFT, self.terminal_rows - 1, padded_text)

    def unknown_command(self, cmd, args):
        self.show(f"Unknown command '{cmd}'")

    def load_file(self, cmd, args):
        """
        :open <path: str> -- opens an image from <path> (requires Pillow)
        """
        filepath, = args
        try:
            image = ImageData.from_file(filepath)
        except Exception as exc:
            self.show(exc)
        else:
            self.draw_area.set_image(image)
            self.full_redraw()

    def save_file(self, cmd, args):
        """
        :save [<path: str>] -- saves the image into <path> (requires Pillow)
        """
        if not args:
            filepath = None
        else:
            filepath, = args
        try:
            self.draw_area.image.save_file(filepath)
        except Exception as exc:
            self.show(exc)
        else:
            self.show(f"Saved image as {self.draw_area.image.filepath}")

    def show_help(self, cmd, args):
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
        self._needs_redraw = True

    def run(self):
        cmd = ""
        for ev in events.listen():
            if self._needs_redraw:
                self.full_redraw()
                self._needs_redraw = False

            if isinstance(ev, events.MouseEvent):
                self._handle_click(ev)
                continue

            if cmd:
                if ev == "backspace":
                    cmd = cmd[:-1]
                    self.show(cmd)
                elif ev == "\n":
                    cmd, *args = cmd.split()
                    self.commands.get(cmd, self.unknown_command)(cmd, args)
                    cmd = ""
                elif not isinstance(ev, events.MouseEvent) and len(ev) == 1:
                    cmd += ev
                    self.show(cmd)
                continue

            if ev in {"q", "ctrl-q"}:
                self.exit()
            elif ev in {":", "ctrl-e"}:
                cmd = ":"
                self.show(cmd)
            elif ev == "?":
                self.commands[":help"](":help", None)
            elif ev == "r":
                self.full_redraw()
            elif ev in set("0123456789"):
                i = int(ev)
                if i < len(self.widgets):
                    self.widgets[i].toggle_selected()
                    self.full_redraw()
            elif ev in {"up", "down", "left", "right"}:
                dx, dy = {
                    "up": (0, -1),
                    "down": (0, +1),
                    "left": (-1, 0),
                    "right": (+1, 0)
                }[ev]
                for widget in self.widgets:
                    if widget.selected:
                        widget.move(dx, dy)
                self.full_redraw()
            elif ev in {"ctrl-up", "ctrl-down", "ctrl-left", "ctrl-right"}:
                for widget in self.widgets:
                    if widget.selected:
                        if ev == "ctrl-up":
                            widget.resize_up()
                        elif ev == "ctrl-down":
                            widget.resize_down()
                        elif ev == "ctrl-left":
                            widget.resize_left()
                        elif ev == "ctrl-right":
                            widget.resize_right()
                self.full_redraw()
            elif ev == "ctrl-s":
                self.commands[":save"](":save", None)
            else:
                self.show(f"got event: {ev!r}")

    def _handle_click(self, ev):
        for widget in reversed(self.widgets):
            if widget.contains(ev.x, ev.y) and widget.onclick(ev):
                return
        if ev.event_type == MouseEventType.MOUSE_UP and self.draw_area.starting_pos is not None:
            self.draw_area.starting_pos = None
            self.full_redraw()
            return
        self.show(f"got event: {ev!r}")

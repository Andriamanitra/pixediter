from colors import Color
import colors
import events
import terminal


def draw(x: int, y: int, text: str, color: Color = colors.WHITE):
    terminal.addstr(y, x, color.colorize(text))


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
        self.TOP = 3
        self.LEFT = 3
        self.BOTTOM = self.TOP + height - 1
        self.RIGHT = self.LEFT + 2 * width - 1

        self.PALETTE_TOP = self.BOTTOM + 3
        self.PALETTE_LEFT = self.LEFT
        self.PALETTE_BOTTOM = self.PALETTE_TOP + 1
        self.PALETTE_RIGHT = self.LEFT + 32 - 1

        self.box_LR = "─"
        self.box_UD = "│"
        self.box_RD = "╭"
        self.box_LD = "╮"
        self.box_RU = "╰"
        self.box_LU = "╯"

        self.FILLED_PIXEL = "██"

        self.terminal_columns, self.terminal_rows = terminal.size()
        self.color = colors.BLACK
        self.palette = {}
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

        self.image = ImageData(width, height)

        self._needs_redraw = False
        self.full_redraw()

    @property
    def draw_area(self):
        return (self.LEFT, self.TOP, self.RIGHT, self.BOTTOM)

    @property
    def palette_area(self):
        return (self.PALETTE_LEFT, self.PALETTE_TOP, self.PALETTE_RIGHT, self.PALETTE_BOTTOM)

    def exit(self, *args):
        """exits the program without saving"""
        terminal.clear()
        raise SystemExit(0)

    def draw_box_around(self, area):
        x0, y0, x1, y1 = area
        self.draw_box(x0 - 1, y0 - 1, x1 + 1, y1 + 1)

    def draw_box(self, x0, y0, x1, y1):
        draw(x0, y0, self.box_RD)
        draw(x1, y0, self.box_LD)
        draw(x0, y1, self.box_RU)
        draw(x1, y1, self.box_LU)
        for x in range(x0 + 1, x1):
            draw(x, y0, self.box_LR)
            draw(x, y1, self.box_LR)
        for y in range(y0 + 1, y1):
            draw(x0, y, self.box_UD)
            draw(x1, y, self.box_UD)

    def draw_title(self):
        draw(4, 1, "PixEdiTer v0.0.1", colors.GREEN)

    def full_redraw(self):
        terminal.clear()
        self.terminal_columns, self.terminal_rows = terminal.size()
        self.width, self.height = terminal.size()
        self.BOTTOM = self.TOP + self.image.height - 1
        self.RIGHT = self.LEFT + 2 * self.image.width - 1
        self.draw_box_around(self.draw_area)
        self.draw_title()
        self.render_image()
        self.draw_box_around(self.palette_area)
        self.set_palette([
            colors.BLACK,
            colors.GRAY,
            colors.WHITE,
            colors.RED,
            colors.YELLOW,
            colors.GREEN,
            colors.CYAN,
            colors.BLUE,
            colors.MAGENTA,
        ])

    def new_image(self, cmd, args):
        """
        :new <width: int> <height: int> -- replaces canvas with a new image of given dimensions
        """
        width, height = args
        width = int(width)
        height = int(height)
        self.image = ImageData(width, height)
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
            self.image.crop(x0, y0, x1, y1)
        except Exception as exc:
            self.show(exc)
        else:
            self.full_redraw()

    def set_color(self, color):
        self.color = color
        self.show(f"Color picked: {self.color} – hex: {self.color.hex()}")

    def terminal_coords_to_img_coords(self, x, y):
        img_x = (x - self.LEFT) // 2
        img_y = y - self.TOP
        return img_x, img_y

    def paint(self, img_x, img_y, color):
        self.image[img_x, img_y] = color
        self.render_pixel(img_x, img_y, color)

    def render_pixel(self, x, y, color):
        # pixels are 2 characters wide
        x = self.LEFT + 2 * x
        y = self.TOP + y
        draw(x, y, self.FILLED_PIXEL, color)

    def render_image(self):
        for (x, y), color in self.image:
            self.render_pixel(x, y, color)

    def set_palette(self, palette):
        color_index = 0
        for y in range(self.PALETTE_TOP, self.PALETTE_BOTTOM + 1):
            for x in range(self.PALETTE_LEFT, self.PALETTE_RIGHT, 2):
                if color_index >= len(palette):
                    color = Color.random()
                else:
                    color = palette[color_index]
                draw(x, y, self.FILLED_PIXEL, color)
                self.palette[(x, y)] = color
                self.palette[(x + 1, y)] = color
                color_index += 1

    def show(self, to_show):
        available_space = self.terminal_columns - self.LEFT
        draw(self.LEFT, self.terminal_rows, str(to_show).ljust(available_space)[:available_space])

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
            self.image = image
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
            self.image.save_file(filepath)
        except Exception as exc:
            self.show(exc)
        else:
            self.show(f"Saved image as {self.image.filepath}")

    def show_help(self, cmd, args):
        """
        shows keybindings and commands
        """
        terminal.clear()
        self.draw_title()
        row_number = 3
        # TODO: support customizable bindings
        draw(self.LEFT, row_number, "Keybindings:", colors.GREEN)
        row_number += 1
        keybindings = {
            "middle click": "pick a color",
            "ctrl-s": "save",
            ":  OR  ctrl-e": "open command line",
            "r": "force redraw",
            "q": "exit without saving",
            "?": "show this help"
        }
        for key, action in keybindings.items():
            draw(self.LEFT + 2, row_number, key, colors.WHITE)
            draw(self.LEFT + 4, row_number + 1, action, colors.GRAY)
            row_number += 2

        row_number += 1
        draw(self.LEFT, row_number, "Commands:", colors.GREEN)
        already_shown = set()
        row_number += 1
        for cmd, func in self.commands.items():
            if func in already_shown:
                continue
            explanation = str(func.__doc__).strip().split("\n")[0]
            draw(self.LEFT + 2, row_number, cmd)
            draw(self.LEFT + 4, row_number + 1, explanation, colors.GRAY)
            already_shown.add(func)
            row_number += 2

        draw(self.LEFT, row_number + 2, "Press any key to continue...")
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

            if ev in ("q", "ctrl-q"):
                self.exit()
            elif ev in (":", "ctrl-e"):
                cmd = ":"
                self.show(cmd)
            elif ev == "?":
                self.commands[":help"](":help", None)
            elif ev == "r":
                self.full_redraw()
            elif ev == "up":
                self.PALETTE_TOP -= 1
                self.PALETTE_BOTTOM -= 1
                self.full_redraw()
            elif ev == "down":
                self.PALETTE_TOP += 1
                self.PALETTE_BOTTOM += 1
                self.full_redraw()
            elif ev == "left":
                self.PALETTE_LEFT -= 1
                self.PALETTE_RIGHT -= 1
                self.full_redraw()
            elif ev == "right":
                self.PALETTE_LEFT += 1
                self.PALETTE_RIGHT += 1
                self.full_redraw()
            elif ev == "ctrl-s":
                self.commands[":save"](":save", None)
            else:
                self.show(f"got event: {ev!r}")

    def _inside(self, area, x, y):
        left, top, right, bottom = area
        return top <= y <= bottom and left <= x <= right

    def _handle_click(self, ev):
        if self._inside(self.palette_area, ev.x, ev.y):
            if ev.button == 0:
                self.set_color(self.palette.get((ev.x, ev.y), colors.WHITE))
        elif self._inside(self.draw_area, ev.x, ev.y):
            img_x, img_y = self.terminal_coords_to_img_coords(ev.x, ev.y)
            if ev.button == 0 or ev.button == 32:  # 32 when mouse is moving
                self.paint(img_x, img_y, self.color)
            elif ev.button == 1:
                self.set_color(self.image[img_x, img_y])
        else:
            self.show(f"got event: {ev!r}")


if __name__ == "__main__":
    app = App(24, 24)
    with terminal.hidden_cursor(), terminal.mouse_tracking():
        app.run()

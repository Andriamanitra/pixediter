from colors import Color
import colors
import borders
import events
import terminal


def draw(x: int, y: int, text: str, color: Color = colors.WHITE):
    terminal.addstr(y, x, color.colorize(text))


def draw_box(x0, y0, x1, y1, box_drawing_chars=borders.sharp, color=colors.WHITE):
    LR, UD, RD, LD, RU, LU = box_drawing_chars
    draw(x0, y0, RD, color=color)
    draw(x1, y0, LD, color=color)
    draw(x0, y1, RU, color=color)
    draw(x1, y1, LU, color=color)
    for x in range(x0 + 1, x1):
        draw(x, y0, LR, color=color)
        draw(x, y1, LR, color=color)
    for y in range(y0 + 1, y1):
        draw(x0, y, UD, color=color)
        draw(x1, y, UD, color=color)


class TerminalWidget:
    def __init__(self, *, parent, bbox, borders=None):
        self.parent = parent
        self.selected = False
        self.left, self.top, self.right, self.bottom = bbox
        self.borders = borders
        self.title = None

    def contains(self, x: int, y: int) -> bool:
        """
        Checks if x and y (terminal coordinates) are inside this widget.
        Borders are not counted as being inside.
        """
        return self.top <= y <= self.bottom and self.left <= x <= self.right

    def move(self, dx: int, dy: int):
        """Moves the widget dx columns to the left and dy rows down"""
        self.left += dx
        self.right += dx
        self.top += dy
        self.bottom += dy

    def toggle_selected(self):
        self.selected = not self.selected

    def onclick(self, ev: events.MouseEvent) -> bool:
        """
        Called when the widget is clicked.
        Should return True if the event is not to be handled by any other widget.
        """
        print(f"Click! ({ev})")
        return False

    def render(self):
        """Draws the widget in the terminal"""
        if self.borders is not None:
            x0, y0 = self.left - 1, self.top - 1
            x1, y1 = self.right + 1, self.bottom + 1
            color = colors.RED if self.selected else colors.WHITE
            draw_box(x0, y0, x1, y1, self.borders, color)
        if self.title is not None:
            draw(self.left, self.top - 1, self.title)

    def resize_up(self):
        if self.bottom > self.top:
            self.bottom -= 1

    def resize_down(self):
        self.bottom += 1

    def resize_left(self):
        if self.right > self.left:
            self.right -= 1

    def resize_right(self):
        self.right += 1


class DrawArea(TerminalWidget):
    def __init__(self, *, parent, bbox, borders=None, image):
        super().__init__(parent=parent, bbox=bbox, borders=borders)
        self.image = image
        self.FILLED_PIXEL = "██"

    def onclick(self, ev: events.MouseEvent):
        img_x, img_y = self.terminal_coords_to_img_coords(ev.x, ev.y)
        if ev.button == 0 or ev.button == 32:  # 32 when mouse is moving
            self.paint(img_x, img_y, self.parent.color)
        elif ev.button == 1:
            self.parent.set_color(self.image[img_x, img_y])
        return True

    def render(self):
        super().render()
        for (x, y), color in self.image:
            self.render_pixel(x, y, color)

    def terminal_coords_to_img_coords(self, x, y):
        img_x = (x - self.left) // 2
        img_y = y - self.top
        return img_x, img_y

    def paint(self, img_x, img_y, color):
        self.image[img_x, img_y] = color
        self.render_pixel(img_x, img_y, color)

    def render_pixel(self, x, y, color):
        # pixels are 2 characters wide
        x = self.left + 2 * x
        y = self.top + y
        draw(x, y, self.FILLED_PIXEL, color)

    def set_image(self, image):
        self.image = image
        self._update_pos()

    def crop(self, x0, y0, x1, y1):
        self.image.crop(x0, y0, x1, y1)
        self._update_pos()

    def _update_pos(self):
        self.right = self.left + 2 * self.image.width - 1
        self.bottom = self.top + self.image.height - 1

    def resize_up(self):
        if self.image.height > 1:
            self.crop(0, 0, self.image.width, self.image.height - 1)

    def resize_down(self):
        self.crop(0, 0, self.image.width, self.image.height + 1)

    def resize_left(self):
        if self.image.width > 1:
            self.crop(0, 0, self.image.width - 1, self.image.height)

    def resize_right(self):
        self.crop(0, 0, self.image.width + 1, self.image.height)


class Palette(TerminalWidget):
    default_colors = [
        colors.BLACK,
        colors.GRAY,
        colors.WHITE,
        colors.RED,
        colors.YELLOW,
        colors.GREEN,
        colors.CYAN,
        colors.BLUE,
        colors.MAGENTA,
    ]

    def __init__(self, *, parent, bbox, borders=None, colors):
        super().__init__(parent=parent, bbox=bbox, borders=borders)
        self._color_from_coord = {}
        self.FILLED_PIXEL = "██"
        self.colors = []
        self.set_colors(colors)

    def onclick(self, ev: events.MouseEvent) -> bool:
        if ev.button == 0 or ev.button == 1:
            color = self._color_from_coord.get((ev.x, ev.y), colors.WHITE)
            self.parent.set_color(color)
        return True

    def move(self, dx: int, dy: int):
        super().move(dx, dy)
        self.set_colors(self.colors)

    def set_colors(self, colors):
        self._color_from_coord = {}
        self.colors = []
        color_index = 0
        for y in range(self.top, self.bottom + 1):
            for x in range(self.left, self.right, 2):
                if color_index >= len(colors):
                    new_color = Color.random()
                else:
                    new_color = colors[color_index]
                self.colors.append(new_color)
                self._color_from_coord[(x, y)] = new_color
                self._color_from_coord[(x + 1, y)] = new_color
                color_index += 1

    def render(self):
        super().render()
        colors = iter(self.colors)
        for y in range(self.top, self.bottom + 1):
            for x in range(self.left, self.right, 2):
                try:
                    color = next(colors)
                except StopIteration:
                    return
                draw(x, y, self.FILLED_PIXEL, color)

    def resize_up(self):
        if self.bottom > self.top:
            self.bottom -= 1

    def resize_down(self):
        self.bottom += 1
        number_of_visible_colors = self.rows * self.cols
        extra_colors_needed = number_of_visible_colors - len(self.colors)
        extra_colors = [Color.random() for i in range(extra_colors_needed)]
        if extra_colors:
            self.set_colors(self.colors + extra_colors)

    def resize_left(self):
        if self.right > self.left + 2:
            self.right -= 2

    def resize_right(self):
        self.right += 2
        number_of_visible_colors = self.rows * self.cols
        extra_colors_needed = number_of_visible_colors - len(self.colors)
        extra_colors = [Color.random() for i in range(extra_colors_needed)]
        if extra_colors:
            self.set_colors(self.colors + extra_colors)

    @property
    def rows(self):
        return self.bottom - self.top + 1

    @property
    def cols(self):
        return (self.right - self.left + 1) // 2


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

        self.widgets = [
            self.draw_area,
            self.palette,
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
        draw(4, 1, "PixEdiTer v0.0.2", colors.GREEN)

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

    def set_color(self, color):
        self.color = color
        self.show(f"Color picked: {self.color} – hex: {self.color.hex()}")

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
            "middle click": "pick a color",
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
        self.show(f"got event: {ev!r}")


if __name__ == "__main__":
    app = App(24, 24)
    with terminal.hidden_cursor(), terminal.mouse_tracking():
        app.run()

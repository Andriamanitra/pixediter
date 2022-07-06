from pixediter import events
from pixediter.events import MouseButton
from pixediter.events import MouseEventType
from pixediter.utils import draw
from pixediter.utils import rect

from .TerminalWidget import TerminalWidget


class DrawArea(TerminalWidget):
    def __init__(self, *, parent, bbox, borders=None, image):
        super().__init__(parent=parent, bbox=bbox, borders=borders)
        self.image = image
        self.FILLED_PIXEL = "██"
        self.starting_pos = None
        self._prev_pos = (-1, -1)

    def onclick(self, ev: events.MouseEvent):
        img_x, img_y = self.terminal_coords_to_img_coords(ev.x, ev.y)

        match self.parent.tool, ev.event_type, ev.button:
            case _, MouseEventType.MOUSE_DOWN, MouseButton.MIDDLE | MouseButton.MIDDLE_DRAG:
                self.parent.set_primary_color(self.image[img_x, img_y])

            case "Pencil", MouseEventType.MOUSE_DOWN, MouseButton.LEFT | MouseButton.LEFT_DRAG:
                self.paint(img_x, img_y, self.parent.color)

            case "Pencil", MouseEventType.MOUSE_DOWN, MouseButton.RIGHT | MouseButton.RIGHT_DRAG:
                self.paint(img_x, img_y, self.parent.secondary_color)

            case "Rectangle", MouseEventType.MOUSE_DOWN, MouseButton.LEFT | MouseButton.RIGHT:
                self.starting_pos = (img_x, img_y)
                self._prev_pos = (img_x, img_y)

            case "Rectangle", MouseEventType.MOUSE_DOWN, MouseButton.LEFT_DRAG | MouseButton.RIGHT_DRAG:
                if self.starting_pos is None:
                    return False

                drawn = set()

                # draw current
                color = self.parent.color
                if ev.button == MouseButton.RIGHT_DRAG:
                    color = self.parent.secondary_color
                start_x, start_y = self.starting_pos
                for x, y in rect(start_x, start_y, img_x, img_y):
                    self.render_pixel(x, y, color)
                    drawn.add((x, y))

                # clean up previous
                for x, y in rect(*self.starting_pos, *self._prev_pos):
                    if (x, y) not in drawn:
                        self.render_pixel(x, y, self.image[x, y])

                self._prev_pos = (img_x, img_y)

            case "Rectangle", MouseEventType.MOUSE_UP, MouseButton.LEFT | MouseButton.RIGHT:
                if self.starting_pos is None:
                    return False
                color = self.parent.color
                if ev.button == MouseButton.RIGHT:
                    color = self.parent.secondary_color
                self.image.paint_rectangle(*self.starting_pos, img_x, img_y, color)
                self.starting_pos = None
                self.parent.full_redraw()

            case "Fill", MouseEventType.MOUSE_DOWN, MouseButton.LEFT | MouseButton.RIGHT:
                from_color = self.image[img_x, img_y]
                to_color = self.parent.color
                if ev.button == MouseButton.RIGHT:
                    to_color = self.parent.secondary_color
                if from_color == to_color:
                    return True
                width = self.image.width
                height = self.image.height
                stack = [(img_x, img_y)]
                visited = set()
                while stack:
                    x, y = xy = stack.pop()
                    if self.image[x, y] != from_color:
                        continue
                    self.paint(x, y, to_color)
                    visited.add(xy)
                    if y > 0 and (x, y - 1) not in visited:
                        stack.append((x, y - 1))
                    if x > 0 and (x - 1, y) not in visited:
                        stack.append((x - 1, y))
                    if y < height - 1 and (x, y + 1) not in visited:
                        stack.append((x, y + 1))
                    if x < width - 1 and (x + 1, y) not in visited:
                        stack.append((x + 1, y))

            case _:
                return False

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

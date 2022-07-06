from pixediter import colors
from pixediter import events
from pixediter.utils import draw
from pixediter.utils import draw_box


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

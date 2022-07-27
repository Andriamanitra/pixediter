from collections.abc import Callable
from typing import Literal

from pixediter.colors import Color


ColorChangeListener = Callable[[str, Color, Color], None]


class ColorSelector:
    def __init__(self, primary: Color, secondary: Color) -> None:
        self.primary = primary
        self.secondary = secondary
        self.on_change_listeners: list[ColorChangeListener] = []

    def add_change_listener(self, fn: ColorChangeListener) -> None:
        self.on_change_listeners.append(fn)

    def set_color(self, which: Literal["primary", "secondary"], color: Color) -> None:
        old_color = getattr(self, which)
        setattr(self, which, color)
        for fn in self.on_change_listeners:
            fn(which, old_color, color)

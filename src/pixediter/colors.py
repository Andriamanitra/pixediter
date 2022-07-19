from __future__ import annotations

import colorsys
import dataclasses
import random

from pixediter import terminal


@dataclasses.dataclass
class Color:
    r: int
    g: int
    b: int

    def hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def rgb(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def hsl(self) -> tuple[float, float, float]:
        h, l, s = colorsys.rgb_to_hls(self.r/255, self.g/255, self.b/255)
        return h, s, l

    def add_rgb(self, red: int, green: int, blue: int) -> Color:
        red += self.r
        green += self.g
        blue += self.b
        red = max(0, min(255, red))
        green = max(0, min(255, green))
        blue = max(0, min(255, blue))
        return Color(red, green, blue)

    def add_hsl(self, hue: float, saturation: float, lightness: float) -> Color:
        H, S, L = self.hsl()
        H += hue
        S += saturation
        L += lightness
        H %= 1.0
        S = max(0.0, min(1.0, S))
        L = max(0.0, min(1.0, L))
        return Color.from_hsl(H, S, L)

    @classmethod
    def from_hex(cls, hexcolor: str) -> Color:
        hexcolor = hexcolor.removeprefix("#")
        hexcolor = hexcolor.removeprefix("0x")
        assert len(hexcolor) == 6
        hexval = int(hexcolor, 16)
        b = hexval & 255
        hexval >>= 8
        g = hexval & 255
        hexval >>= 8
        r = hexval & 255
        return cls(r, g, b)

    @classmethod
    def from_hsl(cls, hue: float, saturation: float, lightness: float) -> Color:
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        return Color(int(255 * r), int(255 * g), int(255 * b))

    @classmethod
    def random(cls) -> Color:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return cls(r, g, b)

    def colorize(self, txt: str) -> str:
        return terminal.colorize(txt, self.r, self.g, self.b)


BLACK = Color(0, 0, 0)
GRAY = Color(127, 127, 127)
WHITE = Color(255, 255, 255)
RED = Color(255, 0, 0)
YELLOW = Color(255, 255, 0)
GREEN = Color(0, 255, 0)
CYAN = Color(0, 255, 255)
BLUE = Color(0, 0, 255)
MAGENTA = Color(255, 0, 255)

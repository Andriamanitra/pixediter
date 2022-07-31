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
        hexval = int(hexcolor, 16)
        if hexval < 0 or hexval > 0xFFFFFF:
            raise ValueError(f"Invalid hex color value '{hexcolor}'")
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

    @classmethod
    def lerp_rgb(cls, color_a: Color, color_b: Color, value: float) -> Color:
        """Linear interpolation between two colors in RGB color space"""
        if value < 0.0 or value > 1.0:
            raise ValueError("Interpolation value has to be between 0 and 1")
        r = round(color_a.r + (color_b.r - color_a.r) * value)
        g = round(color_a.g + (color_b.g - color_a.g) * value)
        b = round(color_a.b + (color_b.b - color_a.b) * value)
        return cls(r, g, b)

    @classmethod
    def lerp_hsl(cls, color_a: Color, color_b: Color, value: float) -> Color:
        """Linear interpolation between two colors in HSL color space"""
        if value < 0.0 or value > 1.0:
            raise ValueError("Interpolation value has to be between 0 and 1")
        h_a, s_a, l_a = color_a.hsl()
        h_b, s_b, l_b = color_b.hsl()
        # since hue is circular (0.0 is the same as 1.0) it needs special handling
        hue_difference = h_b - h_a
        if hue_difference > 0.5:
            hue_difference = -(1.0 - hue_difference)
        elif hue_difference < -0.5:
            hue_difference = -(-1.0 - hue_difference)
        hue = (h_a + hue_difference * value) % 1.0
        saturation = s_a + (s_b - s_a) * value
        lightness = l_a + (l_b - l_a) * value
        return cls.from_hsl(hue, saturation, lightness)

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

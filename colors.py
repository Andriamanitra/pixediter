import dataclasses
import random

import terminal


@dataclasses.dataclass
class Color:
    r: int
    g: int
    b: int

    def hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def rgb(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @classmethod
    def from_hex(cls, hexcolor: str):
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
    def random(cls):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return cls(r, g, b)

    def colorize(self, txt: str):
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

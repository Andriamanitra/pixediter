from __future__ import annotations

from collections.abc import Generator

from pixediter import colors
from pixediter.colors import Color


Pos = tuple[int, int]


class NoFilePathException(Exception):
    pass


class ImageData:
    def __init__(self, width: int = 16, height: int = 16, filepath: str | None = None):
        self.width = width
        self.height = height
        self.filepath = filepath
        self.pixels = [[colors.WHITE for w in range(width)] for h in range(height)]

    @classmethod
    def from_file(cls, filepath: str) -> ImageData:
        from PIL import Image
        with Image.open(filepath) as image:
            width, height = image.size
            new = cls(width, height, filepath)
            for x in range(width):
                for y in range(height):
                    r, g, b = image.getpixel((x, y))
                    new[x, y] = Color(r, g, b)
        return new

    def save_file(self, filepath: str | None = None) -> None:
        if filepath is None:
            if self.filepath is None:
                raise NoFilePathException("Unable to save: file path not given")
            filepath = self.filepath

        from PIL import Image
        image = Image.new("RGB", (self.width, self.height))
        for x in range(self.width):
            for y in range(self.height):
                image.putpixel((x, y), self[x, y].rgb())
        image.save(filepath)
        self.filepath = filepath

    def crop(self, x0: int, y0: int, x1: int, y1: int) -> None:
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

    def paint_rectangle(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
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

    def __iter__(self) -> Generator[tuple[Pos, Color], None, None]:
        for row_index, row in enumerate(self.pixels):
            for col_index, pixel in enumerate(row):
                yield (col_index, row_index), pixel

    def __getitem__(self, xy: Pos) -> Color:
        x, y = xy
        return self.pixels[y][x]

    def __setitem__(self, xy: Pos, color: Color) -> None:
        x, y = xy
        self.pixels[y][x] = color

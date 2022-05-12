import contextlib
import sys
import os


def enable_mouse_tracking():
    sys.stdout.write("\033[?1000;1002;1006;1015h")
    sys.stdout.flush()


def disable_mouse_tracking():
    sys.stdout.write("\033[?1000;1002;1006;1015l")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\x1b[?25h")
    sys.stdout.flush()


def size() -> tuple[int, int]:
    return os.get_terminal_size()


def clear():
    sys.stdout.write("\033[2J")


def colorize(text: str, r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"


def addstr(row: int, col: int, text: str):
    sys.stdout.write(f"\x1b7\x1b[{row};{col}f{text}\x1b8")
    sys.stdout.flush()


@contextlib.contextmanager
def hidden_cursor():
    hide_cursor()
    try:
        yield
    finally:
        show_cursor()


@contextlib.contextmanager
def mouse_tracking():
    enable_mouse_tracking()
    try:
        yield
    finally:
        disable_mouse_tracking()

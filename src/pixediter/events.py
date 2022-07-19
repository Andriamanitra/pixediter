import dataclasses
import enum
import sys
import termios
import tty
from collections.abc import Generator
from collections.abc import Iterator
from contextlib import contextmanager


NAMED_EVENTS = {
    "\x1b[A":     "up",
    "\x1b[B":     "down",
    "\x1b[C":     "right",
    "\x1b[D":     "left",
    "\x7f":       "backspace",
    "\x11":       "ctrl-q",
    "\x05":       "ctrl-e",
    "\x13":       "ctrl-s",
    "\x1b[1;5A":  "ctrl-up",
    "\x1b[1;5B":  "ctrl-down",
    "\x1b[1;5C":  "ctrl-right",
    "\x1b[1;5D":  "ctrl-left",
}


class MouseButton(enum.Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2
    ALT_LEFT = 8
    ALT_MIDDLE = 9
    ALT_RIGHT = 10
    CTRL_LEFT = 16
    CTRL_MIDDLE = 17
    CTRL_RIGHT = 18
    LEFT_DRAG = 32
    MIDDLE_DRAG = 33
    RIGHT_DRAG = 34
    ALT_LEFT_DRAG = 40
    ALT_MIDDLE_DRAG = 41
    ALT_RIGHT_DRAG = 42
    CTRL_LEFT_DRAG = 48
    CTRL_MIDDLE_DRAG = 49
    CTRL_RIGHT_DRAG = 50
    SCROLL_UP = 64
    SCROLL_DOWN = 65
    ALT_SCROLL_UP = 72
    ALT_SCROLL_DOWN = 73


class MouseEventType(enum.Enum):
    MOUSE_DOWN = "M"
    MOUSE_UP = "m"


@dataclasses.dataclass
class MouseEvent:
    event_type: MouseEventType
    button: MouseButton
    x: int
    y: int

    @classmethod
    def parse(cls, event_str: str) -> "MouseEvent":
        # a valid mouse event is something like:
        # \x1b[<0;51;31M
        # the three numbers are:
        # 1. mouse button
        # 2. y coordinate of the character under cursor
        # 3. x coordinate of the character under cursor
        # the last character is the event type
        mbutton, x, y = event_str[3:-1].split(";")
        event_type = MouseEventType(event_str[-1])
        return cls(event_type, MouseButton(int(mbutton)), int(x), int(y))

    def __repr__(self) -> str:
        return f"MouseEvent({self.event_type.name}, {self.button}, x={self.x}, y={self.y})"


@contextmanager
def setcbreak(fd: int) -> Iterator[None]:
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


@contextmanager
def mouse_tracking_enabled() -> Iterator[None]:
    ENABLE_MOUSE_TRACKING = "\033[?1000;1002;1006;1015h"
    DISABLE_MOUSE_TRACKING = "\033[?1000;1002;1006;1015l"
    try:
        print(ENABLE_MOUSE_TRACKING, end="", flush=True)
        yield
    finally:
        print(DISABLE_MOUSE_TRACKING, end="", flush=True)


def listen() -> Generator[MouseEvent | str, None, None]:
    with setcbreak(sys.stdin.fileno()):
        while True:
            event = sys.stdin.read(1)
            if event == "\x1b":  # ESC
                # i think most escape sequences end with alphabetic character?
                # seems to work fine for now at least
                while not event[-1].isalpha():
                    event += sys.stdin.read(1)
                if event.startswith("\x1b[<"):
                    yield MouseEvent.parse(event)
                    continue
            if event in NAMED_EVENTS:
                yield NAMED_EVENTS[event]
            else:
                yield event


def main() -> int:
    print("tracking events, press enter to stop...")
    for ev in listen():
        print(repr(ev))
        if ev == "\n":
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

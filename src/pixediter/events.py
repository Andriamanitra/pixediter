from __future__ import annotations

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
    SHIFT_LEFT = 4
    SHIFT_MIDDLE = 5
    SHIFT_RIGHT = 6
    ALT_LEFT = 8
    ALT_MIDDLE = 9
    ALT_RIGHT = 10
    ALT_SHIFT_LEFT = 12
    ALT_SHIFT_MIDDLE = 13
    ALT_SHIFT_RIGHT = 14
    CTRL_LEFT = 16
    CTRL_MIDDLE = 17
    CTRL_RIGHT = 18
    CTRL_SHIFT_LEFT = 20
    CTRL_SHIFT_MIDDLE = 21
    CTRL_SHIFT_RIGHT = 22
    CTRL_ALT_LEFT = 24
    CTRL_ALT_MIDDLE = 25
    CTRL_ALT_RIGHT = 26
    CTRL_ALT_SHIFT_LEFT = 28
    CTRL_ALT_SHIFT_MIDDLE = 29
    CTRL_ALT_SHIFT_RIGHT = 30
    SCROLL_UP = 64
    SCROLL_DOWN = 65
    ALT_SCROLL_UP = 72
    ALT_SCROLL_DOWN = 73

    # When initializing through MouseEvent, these should never happen
    # because it stores MOUSE_DRAG separately in MouseEventType
    LEFT_DRAG = 32
    MIDDLE_DRAG = 33
    RIGHT_DRAG = 34
    ALT_LEFT_DRAG = 40
    ALT_MIDDLE_DRAG = 41
    ALT_RIGHT_DRAG = 42
    CTRL_LEFT_DRAG = 48
    CTRL_MIDDLE_DRAG = 49
    CTRL_RIGHT_DRAG = 50

    def left(self) -> bool:
        return self.value < 64 and self.value & 3 == 0

    def middle(self) -> bool:
        return self.value < 64 and self.value & 3 == 1

    def right(self) -> bool:
        return self.value < 64 and self.value & 3 == 2

    def shift(self) -> bool:
        return self.value & 4 == 4

    def alt(self) -> bool:
        return self.value & 8 == 8

    def ctrl(self) -> bool:
        return self.value & 16 == 16


class MouseEventType(enum.Enum):
    MOUSE_DOWN = "M"
    MOUSE_UP = "m"
    # dragging does not come directly from terminal escape sequence
    MOUSE_DRAG = "DRAG"


@dataclasses.dataclass
class MouseEvent:
    event_type: MouseEventType
    button: MouseButton
    x: int
    y: int

    @classmethod
    def parse(cls, event_str: str) -> MouseEvent:
        # a valid mouse event is something like:
        # \x1b[<0;51;31M
        # the three numbers are:
        # 1. mouse button
        # 2. y coordinate of the character under cursor
        # 3. x coordinate of the character under cursor
        # the last character is the event type
        mbutton, x, y = event_str[3:-1].split(";")
        button_num = int(mbutton)
        if button_num & 32 == 32:
            event_type = MouseEventType.MOUSE_DRAG
            button_num -= 32
        else:
            event_type = MouseEventType(event_str[-1])
        return cls(event_type, MouseButton(button_num), int(x), int(y))

    @property
    def is_drag(self) -> bool:
        return self.button.value & 32 == 32

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

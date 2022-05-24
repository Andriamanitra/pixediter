import sys
import tty
import contextlib
import termios
import dataclasses


@dataclasses.dataclass
class MouseEvent:
    event_type: str
    button: int
    x: int
    y: int

    @classmethod
    def parse(cls, event_str: str):
        # a valid mouse event is something like:
        # \x1b[<0;51;31M
        # the three numbers are:
        # 1. mouse button
        # 2. y coordinate of the character under cursor
        # 3. x coordinate of the character under cursor
        # the last character is the event type
        event_types = {
            "M": "mousedown",
            "m": "mouseup",
        }
        try:
            mbutton, x, y = map(int, event_str[3:-1].split(";"))
            event_type = event_types[event_str[-1]]
            return cls(event_type, mbutton, x, y)
        except Exception:  # this is stupid but works for now
            return event_str


@contextlib.contextmanager
def setcbreak(fd):
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


@contextlib.contextmanager
def mouse_tracking_enabled():
    ENABLE_MOUSE_TRACKING = "\033[?1000;1002;1006;1015h"
    DISABLE_MOUSE_TRACKING = "\033[?1000;1002;1006;1015l"
    try:
        print(ENABLE_MOUSE_TRACKING, end="", flush=True)
        yield
    finally:
        print(DISABLE_MOUSE_TRACKING, end="", flush=True)


def listen():
    with setcbreak(sys.stdin.fileno()):
        while True:
            event = sys.stdin.read(1)
            if event == "\x1b":  # ESC
                # i think most escape sequences end with alphabetic character?
                # seems to work fine for now at least
                while not event[-1].isalpha():
                    event += sys.stdin.read(1)
                if event.startswith("\x1b[<"):
                    event = MouseEvent.parse(event)
                elif event == "\x1b[A":
                    event = "up"
                elif event == "\x1b[B":
                    event = "down"
                elif event == "\x1b[C":
                    event = "right"
                elif event == "\x1b[D":
                    event = "left"
            # TODO: i'm sure there's a better way to do this
            if event == "\x7f":
                event = "backspace"
            if event == "\x11":
                event = "ctrl-q"
            if event == "\x05":
                event = "ctrl-e"
            if event == "\x13":
                event = "ctrl-s"
            if event == "\x1b[1;5A":
                event = "ctrl-up"
            if event == "\x1b[1;5B":
                event = "ctrl-down"
            if event == "\x1b[1;5C":
                event = "ctrl-right"
            if event == "\x1b[1;5D":
                event = "ctrl-left"
            yield event


if __name__ == "__main__":
    print("tracking events, press enter to stop...")
    for event in listen():
        print(repr(event))
        if event == "\n":
            break

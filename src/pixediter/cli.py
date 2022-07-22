import argparse

from pixediter import terminal
from pixediter.application import App


def size(wxh: str):
    """Parses string "WIDTHxHEIGHT" into a tuple (WIDTH, HEIGHT)"""
    if "x" not in wxh:
        raise argparse.ArgumentTypeError("You need to specify both WIDTH and HEIGHT separated by 'x'")
    try:
        width, _, height = wxh.partition("x")
        return int(width), int(height)
    except Exception as exc:
        raise argparse.ArgumentTypeError(exc)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--size",
        type=size,
        default=(24, 24),
        metavar="WIDTHxHEIGHT",
        help="Size of the canvas"
    )
    args = parser.parse_args()

    width, height = args.size
    app = App(width, height)

    with terminal.hidden_cursor(), terminal.mouse_tracking():
        app.run()


if __name__ == "__main__":
    main()

import argparse
import os

from pixediter import terminal
from pixediter.application import App


def size(wxh: str) -> tuple[int, int]:
    """Parses string "WIDTHxHEIGHT" into a tuple (WIDTH, HEIGHT)"""
    if "x" not in wxh:
        raise argparse.ArgumentTypeError("You need to specify both WIDTH and HEIGHT separated by 'x'")
    try:
        width, _, height = wxh.partition("x")
        return int(width), int(height)
    except Exception as exc:
        raise argparse.ArgumentTypeError(exc)


def path(file_path: str) -> str:
    """
    Check that path either
     a) exists and is a file
     OR
     b) does not exist and parent directory can be written to
    """
    fpath = os.path.expanduser(file_path)

    if os.path.exists(fpath):
        if os.path.isfile(fpath):
            return fpath
        else:
            raise argparse.ArgumentTypeError("No file at the given path")

    directory = os.path.dirname(fpath)
    if not os.path.exists(directory):
        raise argparse.ArgumentTypeError(f"Directory '{directory}' does not exist")
    if not os.access(directory, os.W_OK):
        raise argparse.ArgumentTypeError(f"You don't have permissions to write to '{directory}'")
    return fpath


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--size",
        type=size,
        default=(24, 24),
        metavar="WIDTHxHEIGHT",
        help="Size of the canvas"
    )
    parser.add_argument(
        "image_file_path",
        metavar="FILE",
        nargs="?",
        type=path,
        default=None,
        help="(optional) Path to image file"
    )
    args = parser.parse_args()
    width, height = args.size
    file_path = args.image_file_path

    app = App(width, height)

    if file_path is not None:
        if os.path.exists(file_path):
            app.load_image(file_path)
        else:
            app.set_image_file_path(file_path)

    with terminal.hidden_cursor(), terminal.mouse_tracking():
        app.run()


if __name__ == "__main__":
    main()

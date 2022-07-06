from pixediter import terminal
from pixediter.application import App


def main() -> None:
    app = App(24, 24)
    with terminal.hidden_cursor(), terminal.mouse_tracking():
        app.run()


if __name__ == "__main__":
    main()

# PixEdiTer

Pixel graphics Editor in Terminal


## What?
* Terminal based image editor that supports mouse interaction
* Implemented in Python
* Saving and opening images requires [Pillow](https://github.com/python-pillow/Pillow), but you can try it out without installing anything other than Python (3.10+)

## Why?
I came across [cmdpxl](https://github.com/knosmos/cmdpxl/) and thought it was a rather cool project, but its usefulness is limited by the lack of mouse support. I figured something similar but with a focus on mouse support would be pretty fun to work on and maybe even slightly useful for some very light editing tasks.

## How to use?

### Option 1: Install
1. Clone this repository: `git clone https://github.com/Andriamanitra/pixediter`
1. Navigate to the project directory: `cd pixediter`
1. Create a virtual environment: `python3.10 -m virtualenv venv && . venv/bin/activate`
1. Install the package (along with optional dependencies): `pip install .`
1. Run the executable: `pixediter`

### Option 2: Without installation
1. Clone this repository: `git clone https://github.com/Andriamanitra/pixediter`
1. Navigate to the `src/` directory: `cd pixediter/src`
1. Run the module: `python3.10 -m pixediter`


## Demo
(it looks a bit better in a real terminal, the lines between characters are only there because of asciinema)

[![asciicast](https://asciinema.org/a/3pdHgc24eIIM0qkkhCUeWbRdu.svg)](https://asciinema.org/a/3pdHgc24eIIM0qkkhCUeWbRdu)


## TODO / What next?
* Test with different terminal emulators, I have no idea if it works in anything other than mine currently
* Write some unit tests
* Read key bindings, color pallettes and layouts from a configuration file
* Undo functionality would be nice
* Add more tools:
  * Bezier curves
  * Circles / Ellipses
  * Alpha channel / blending
  * Filters (grayscale, tweak color balance, etc.)
* Eventually it would be nice to have built-in support for [XDG cursor themes](https://wiki.archlinux.org/title/Cursor_themes). The file formats are a bit weird and they are not the most straight-forward thing to work with manually, so PixEdiTer could possibly help with that. Of course it would be rather limited in what kind of resolution it is feasible to work with.
* Having a preview of images in their natural size (in terminals that support images) would be super cool

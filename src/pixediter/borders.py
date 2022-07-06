from collections import namedtuple

Borders = namedtuple("Borders", ["LR", "UD", "RD", "LD", "RU", "LU"])
sharp = Borders("─", "│", "┌", "┐", "└", "┘")
rounded = Borders("─", "│", "╭", "╮", "╰", "╯")
double = Borders("═", "║", "╔", "╗", "╚", "╝")

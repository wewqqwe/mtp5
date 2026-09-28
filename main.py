"""Точка входа лабораторной №5."""

from __future__ import annotations

import os

from logic import Clicker, ColorBoard, calculate, tab_body, tab_titles


def demo() -> None:
    print("калькулятор", calculate(2, "+", 3))
    titles = tab_titles()
    print("вкладки", titles[0], tab_body(titles[0]))
    print("вкладки", titles[1], tab_body(titles[1]))
    board = ColorBoard()
    print("цвет", board.apply("#112233"))
    clicker = Clicker()
    print("кликер", clicker.click())


def main() -> None:
    if os.environ.get("MTP_HEADLESS") == "1":
        demo()
        return
    from ui import build, tk

    if tk is None:
        demo()
        return
    root = tk.Tk()
    build(root)
    root.mainloop()


if __name__ == "__main__":
    main()

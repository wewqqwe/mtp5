"""Точка входа лабораторной №5."""

from __future__ import annotations

import os

from logic import Clicker, ColorBoard, calculate, present_result, tab_body, tab_titles


def demo() -> None:
    print("калькулятор", calculate(2, "+", 3))
    print("калькулятор ошибка", present_result("1", "/", "0"))
    titles = tab_titles()
    print("вкладки", titles[0], tab_body(titles[0]))
    print("вкладки", titles[1], tab_body(titles[1]))
    board = ColorBoard()
    print("цвет", board.apply("#112233"))
    clicker = Clicker()
    print("кликер", clicker.click())
    clicker.reset()
    clicker.start_round()
    print("кликер раунд", clicker.seconds_left, "рекорд", clicker.best)


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

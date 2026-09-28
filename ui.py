"""Виджеты Tkinter: Notebook, калькулятор, цвет, кликер, SQLite."""

from __future__ import annotations

from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    tk = None
    ttk = None

from logic import (
    Clicker,
    ColorBoard,
    SqliteShelf,
    calculate,
    tab_body,
    tab_titles,
)


def build(root):
    if tk is None or ttk is None:
        raise RuntimeError("tkinter unavailable")
    root.title("Вариант 3 — окно")
    nb = ttk.Notebook(root)
    for title in tab_titles():
        page = ttk.Frame(nb)
        ttk.Label(page, text=tab_body(title)).pack(anchor="w", padx=8, pady=8)
        nb.add(page, text=title)
    nb.pack(fill="both", expand=True)

    calc = ttk.LabelFrame(root, text="калькулятор")
    left = ttk.Entry(calc, width=8)
    operator = ttk.Entry(calc, width=3)
    right = ttk.Entry(calc, width=8)
    result = ttk.Label(calc, text="—")
    left.pack(side="left")
    operator.pack(side="left")
    right.pack(side="left")
    result.pack(side="left", padx=6)

    def on_calculate() -> None:
        value = calculate(float(left.get()), operator.get(), float(right.get()))
        result.configure(text=str(value))

    ttk.Button(calc, text="=", command=on_calculate).pack(side="left")
    calc.pack(fill="x", padx=8, pady=4)

    board = ColorBoard()
    swatch = tk.Label(root, text=board.current, bg=board.current)

    def on_color() -> None:
        painted = board.apply("#2255aa")
        swatch.configure(text=painted, bg=painted)

    tk.Button(root, text="Сменить цвет", command=on_color).pack()
    swatch.pack(fill="x")

    clicker = Clicker()
    score = ttk.Label(root, text="0")

    def on_click() -> None:
        score.configure(text=str(clicker.click()))

    tk.Button(root, text="Клик", command=on_click).pack()
    score.pack()

    shelf = SqliteShelf(Path(__file__).with_name("shelf.db"))
    goods_name = ttk.Entry(root)

    def on_goods() -> None:
        shelf.add(goods_name.get() or "без имени")

    goods_name.pack()
    tk.Button(root, text="Добавить goods", command=on_goods).pack()

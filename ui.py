"""Виджеты Tkinter: Notebook, калькулятор, цвет, кликер, SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    tk = None
    ttk = None

from logic import (
    ActionLog,
    Clicker,
    ColorBoard,
    SqliteShelf,
    calculate,
    parse_operands,
    tab_body,
    tab_titles,
)


def build(root, db_path: Path | None = None, best_path: Path | None = None):
    if tk is None or ttk is None:
        raise RuntimeError("tkinter unavailable")
    root.title("Вариант 3 — окно")
    root.minsize(480, 640)
    journal = build_notebook(root)
    build_calculator(root, journal)
    build_color(root)
    best_file = (
        Path(best_path)
        if best_path is not None
        else Path(__file__).with_name("clicker_best.txt")
    )
    stop_clicker = build_clicker(root, best_file)
    db_file = (
        Path(db_path)
        if db_path is not None
        else Path(__file__).with_name("shelf.db")
    )
    shelf = build_db(root, db_file)
    bind_close(root, stop_clicker, shelf)
    return shelf


def build_notebook(root):
    nb = ttk.Notebook(root)
    journal = None
    for title in tab_titles():
        page = ttk.Frame(nb)
        label = ttk.Label(
            page,
            text=tab_body(title),
            justify="left",
            wraplength=440,
        )
        label.pack(anchor="w", padx=8, pady=8)
        if title == "журнал":
            journal = label
        nb.add(page, text=title)
    nb.pack(fill="both", expand=True, padx=8, pady=4)
    if journal is None:
        raise RuntimeError("вкладка журнала не создана")
    return journal


def build_calculator(root, journal) -> None:
    actions = ActionLog()
    calc = ttk.LabelFrame(root, text="калькулятор")
    row = ttk.Frame(calc)
    row.pack(fill="x", padx=4, pady=4)
    left = ttk.Entry(row, width=10)
    operator = ttk.Combobox(
        row,
        width=4,
        values=["+", "-", "*", "/"],
        state="readonly",
    )
    operator.current(0)
    right = ttk.Entry(row, width=10)
    left.pack(side="left")
    operator.pack(side="left", padx=4)
    right.pack(side="left")
    result = ttk.Label(calc, text="—")
    result.pack(anchor="w", padx=6, pady=2)

    def on_calculate() -> None:
        try:
            left_num, sign, right_num = parse_operands(
                left.get(), operator.get(), right.get()
            )
            shown = str(calculate(left_num, sign, right_num))
        except ZeroDivisionError:
            result.configure(text="ошибка: деление на ноль")
            return
        except ValueError:
            result.configure(text="ошибка: нужны числа и операция + - * /")
            return
        result.configure(text=shown)
        journal.configure(
            text=actions.record(
                f"{left.get().strip()} {sign} {right.get().strip()} = {shown}"
            )
        )

    ttk.Button(row, text="=", command=on_calculate).pack(side="left", padx=4)
    calc.pack(fill="x", padx=8, pady=4)


def build_color(root) -> None:
    frame = ttk.LabelFrame(root, text="цвет панели")
    frame.pack(fill="x", padx=8, pady=4)
    board = ColorBoard()
    swatch = tk.Label(frame, text=board.current, bg=board.current, height=2)

    def on_color() -> None:
        painted = board.apply("#2255aa")
        swatch.configure(text=painted, bg=painted)

    ttk.Button(frame, text="Сменить цвет", command=on_color).pack(pady=4)
    swatch.pack(fill="x", padx=4, pady=(0, 4))


def build_clicker(root, best_path: Path):
    frame = ttk.LabelFrame(root, text="кликер")
    frame.pack(fill="x", padx=8, pady=4)
    clicker = Clicker(best_path=best_path)
    status = ttk.Label(frame, text=clicker.status(), wraplength=440, justify="left")
    status.pack(anchor="w", padx=4, pady=4)
    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", padx=4, pady=(0, 4))
    job = {"id": None}
    alive = {"ok": True}

    def paint() -> None:
        if alive["ok"]:
            status.configure(text=clicker.status())

    def cancel() -> None:
        if job["id"] is not None:
            root.after_cancel(job["id"])
            job["id"] = None

    def tick() -> None:
        job["id"] = None
        if not alive["ok"] or not clicker.running:
            paint()
            return
        clicker.tick()
        paint()
        if alive["ok"] and clicker.running:
            job["id"] = root.after(1000, tick)

    def on_click() -> None:
        clicker.click()
        paint()

    def on_start() -> None:
        cancel()
        clicker.start_round()
        paint()
        job["id"] = root.after(1000, tick)

    def on_reset() -> None:
        cancel()
        clicker.reset()
        paint()

    def on_auto() -> None:
        clicker.toggle_auto()
        paint()

    def stop() -> None:
        alive["ok"] = False
        cancel()

    ttk.Button(buttons, text="Клик", command=on_click).pack(side="left")
    ttk.Button(buttons, text="Старт раунда", command=on_start).pack(
        side="left", padx=4
    )
    ttk.Button(buttons, text="Сброс", command=on_reset).pack(side="left")
    ttk.Button(buttons, text="Автоклик", command=on_auto).pack(side="left", padx=4)
    return stop


def build_db(root, db_path: Path):
    frame = ttk.LabelFrame(root, text="SQLite: goods")
    frame.pack(fill="both", expand=True, padx=8, pady=4)
    table = ttk.Frame(frame)
    table.pack(fill="both", expand=True, padx=4, pady=4)
    tree = ttk.Treeview(
        table,
        columns=("id", "name"),
        show="headings",
        height=6,
    )
    tree.heading("id", text="id")
    tree.heading("name", text="название")
    tree.column("id", width=48, stretch=False)
    tree.column("name", width=280)
    scroll = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    goods_name = ttk.Entry(frame)
    goods_name.pack(fill="x", padx=4)
    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", padx=4, pady=4)
    status = ttk.Label(frame, text="записей: 0")
    status.pack(anchor="w", padx=4, pady=(0, 4))
    shelf = SqliteShelf(db_path)

    def refill() -> int:
        for item in tree.get_children():
            tree.delete(item)
        count = 0
        for row in shelf.list():
            loaded = shelf.get(int(row["id"]))
            if loaded is None:
                continue
            tree.insert(
                "",
                "end",
                iid=str(loaded["id"]),
                values=(loaded["id"], loaded["name"]),
            )
            count += 1
        return count

    def selected_id() -> int | None:
        picked = tree.selection()
        if not picked:
            return None
        return int(picked[0])

    def on_add() -> None:
        name = goods_name.get().strip()
        if not name:
            status.configure(text="ошибка: введите название")
            return
        try:
            row_id = shelf.add(name)
        except (ValueError, sqlite3.Error) as error:
            status.configure(text=f"ошибка: {error}")
            return
        loaded = shelf.get(row_id)
        goods_name.delete(0, "end")
        refill()
        title = loaded["name"] if loaded else name
        status.configure(text=f"добавлено: {title}")

    def on_update() -> None:
        row_id = selected_id()
        name = goods_name.get().strip()
        if row_id is None:
            status.configure(text="ошибка: выберите строку")
            return
        if not name:
            status.configure(text="ошибка: введите название")
            return
        try:
            changed = shelf.update(row_id, name)
        except (ValueError, sqlite3.Error) as error:
            status.configure(text=f"ошибка: {error}")
            return
        if not changed:
            status.configure(text="ошибка: запись не найдена")
            return
        loaded = shelf.get(row_id)
        goods_name.delete(0, "end")
        refill()
        title = loaded["name"] if loaded else name
        status.configure(text=f"обновлено: {title}")

    def on_delete() -> None:
        row_id = selected_id()
        if row_id is None:
            status.configure(text="ошибка: выберите строку")
            return
        loaded = shelf.get(row_id)
        if loaded is None or not shelf.delete(row_id):
            status.configure(text="ошибка: запись не найдена")
            refill()
            return
        goods_name.delete(0, "end")
        refill()
        status.configure(text=f"удалено: {loaded['name']}")

    def on_select(_event=None) -> None:
        row_id = selected_id()
        if row_id is None:
            return
        loaded = shelf.get(row_id)
        if loaded is None:
            status.configure(text="ошибка: запись не найдена")
            return
        goods_name.delete(0, "end")
        goods_name.insert(0, str(loaded["name"]))
        status.configure(text=f"выбрано #{loaded['id']}: {loaded['name']}")

    tree.bind("<<TreeviewSelect>>", on_select)
    ttk.Button(buttons, text="Добавить", command=on_add).pack(side="left")
    ttk.Button(buttons, text="Изменить", command=on_update).pack(side="left", padx=4)
    ttk.Button(buttons, text="Удалить", command=on_delete).pack(side="left")
    count = refill()
    status.configure(text=f"записей: {count}")
    return shelf


def bind_close(root, stop_clicker, shelf: SqliteShelf) -> None:
    def close_window() -> None:
        if getattr(root, "_mtp_closed", False):
            return
        root._mtp_closed = True
        stop_clicker()
        shelf.close()
        try:
            if root.winfo_exists():
                root.destroy()
        except tk.TclError:
            return

    def on_destroy(event) -> None:
        if event.widget is not root or getattr(root, "_mtp_closed", False):
            return
        root._mtp_closed = True
        stop_clicker()
        shelf.close()

    root.protocol("WM_DELETE_WINDOW", close_window)
    root.bind("<Destroy>", on_destroy, add="+")

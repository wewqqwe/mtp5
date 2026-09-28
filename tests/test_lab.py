from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from logic import (
    ActionLog,
    Clicker,
    ColorBoard,
    SqliteShelf,
    calculate,
    present_result,
    tab_body,
    tab_titles,
)

ROOT = Path(__file__).resolve().parents[1]


def test_calculate() -> None:
    assert calculate(2, "+", 3) == 5
    assert calculate(9, "-", 4) == 5
    assert calculate(6, "*", 7) == 42
    assert calculate(9, "/", 3) == 3.0
    with pytest.raises(ZeroDivisionError):
        calculate(1, "/", 0)


def test_present_result_reports_input_errors() -> None:
    assert present_result("2", "+", "3") == "5.0"
    assert present_result("2,5", "+", "1,5") == "4.0"
    assert present_result("8", "/", "2") == "4.0"
    assert present_result("6", "*", "7") == "42.0"
    assert present_result("", "+", "1") == "ошибка: нужны числа и операция + - * /"
    assert present_result("abc", "*", "2") == "ошибка: нужны числа и операция + - * /"
    assert present_result("1", "?", "2") == "ошибка: нужны числа и операция + - * /"
    assert present_result("1", "/", "0") == "ошибка: деление на ноль"


def test_journal_records_actions() -> None:
    log = ActionLog()
    assert "Журнал пуст" in log.text()
    saved = log.record("2 + 3 = 5")
    assert "2 + 3 = 5" in saved
    assert saved != tab_body("формулы")


def test_two_tabs_differ() -> None:
    titles = tab_titles()
    assert len(titles) == 2
    assert tab_body(titles[0]) != tab_body(titles[1])
    assert tab_body(titles[0])
    assert tab_body(titles[1])


def test_color_changes() -> None:
    board = ColorBoard()
    assert board.apply("#112233") == "#112233"
    assert board.current == "#112233"


def test_clicker_increments() -> None:
    clicker = Clicker()
    assert clicker.score == 0
    assert clicker.click() == 1
    assert clicker.click() == 2


def test_clicker_round_level_and_best(tmp_path: Path) -> None:
    clicker = Clicker(round_seconds=2)
    for _ in range(10):
        clicker.click()
    assert clicker.score == 10
    assert clicker.best == 10
    assert clicker.level == 2
    assert clicker.goal == 15
    path = tmp_path / "best.txt"
    clicker.save_best(path)
    fresh = Clicker()
    assert fresh.load_best(path) == 10
    clicker.reset()
    assert clicker.score == 0
    assert clicker.best == 10
    assert clicker.running is False
    assert "ожидание" in clicker.status()
    clicker.toggle_auto()
    clicker.start_round()
    assert clicker.running is True
    assert "раунд идёт" in clicker.status()
    assert clicker.tick() == 1
    assert clicker.score == 1
    assert clicker.tick() == 0
    assert clicker.running is False
    assert clicker.score == 2
    assert "раунд окончен" in clicker.status()


def test_sqlite_shelf(tmp_path: Path) -> None:
    shelf = SqliteShelf(tmp_path / "goods.db")
    row_id = shelf.add("тетрадь")
    loaded = shelf.get(row_id)
    assert loaded is not None
    assert loaded["name"] == "тетрадь"
    raw = sqlite3.connect(tmp_path / "goods.db")
    assert raw.execute("SELECT name FROM goods").fetchone()[0] == "тетрадь"
    raw.close()
    assert shelf.list() == [{"id": row_id, "name": "тетрадь"}]
    assert shelf.update(row_id, "ручка")
    assert shelf.get(row_id)["name"] == "ручка"
    assert shelf.delete(row_id)
    assert shelf.get(row_id) is None
    assert shelf.list() == []
    assert shelf.delete(row_id) is False
    with pytest.raises(ValueError):
        shelf.add("   ")
    shelf.close()
    assert shelf.conn is None


def _descendants(widget):
    found = []
    for child in widget.winfo_children():
        found.append(child)
        found.extend(_descendants(child))
    return found


def _text(widget) -> str:
    try:
        return str(widget.cget("text"))
    except Exception:
        return ""


def test_window_calculator_and_goods(tmp_path: Path) -> None:
    pytest.importorskip("tkinter")
    import tkinter as tk

    from ui import build

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("нет дисплея")
    shelf = None
    try:
        shelf = build(
            root,
            db_path=tmp_path / "goods.db",
            best_path=tmp_path / "best.txt",
        )
        root.update_idletasks()
        widgets = _descendants(root)
        classes = {item.winfo_class() for item in widgets}
        assert "TNotebook" in classes
        assert "Treeview" in classes
        assert "TCombobox" in classes

        entries = [item for item in widgets if item.winfo_class() == "TEntry"]
        assert len(entries) >= 3
        left_entry, right_entry, goods = entries[0], entries[1], entries[2]
        combo = next(item for item in widgets if item.winfo_class() == "TCombobox")
        equals = next(item for item in widgets if _text(item) == "=")
        result = next(item for item in widgets if _text(item) == "—")

        equals.invoke()
        assert result.cget("text") == "ошибка: нужны числа и операция + - * /"

        left_entry.insert(0, "2,5")
        right_entry.insert(0, "1,5")
        combo.set("+")
        equals.invoke()
        assert result.cget("text") == "4.0"
        assert any("4.0" in _text(item) for item in _descendants(root))

        left_entry.delete(0, "end")
        right_entry.delete(0, "end")
        left_entry.insert(0, "1")
        right_entry.insert(0, "0")
        combo.set("/")
        equals.invoke()
        assert result.cget("text") == "ошибка: деление на ноль"

        combo.set("?")
        left_entry.delete(0, "end")
        right_entry.delete(0, "end")
        left_entry.insert(0, "3")
        right_entry.insert(0, "4")
        equals.invoke()
        assert result.cget("text").startswith("ошибка")

        goods.insert(0, "тетрадь")
        add = next(item for item in widgets if _text(item) == "Добавить")
        add.invoke()
        assert goods.get() == ""
        tree = next(item for item in widgets if item.winfo_class() == "Treeview")
        rows = tree.get_children()
        assert len(rows) == 1
        assert tree.item(rows[0], "values")[1] == "тетрадь"
        assert any(
            _text(item).startswith("добавлено:") for item in _descendants(root)
        )

        add.invoke()
        assert tree.get_children() == rows
        assert any(
            "введите название" in _text(item) for item in _descendants(root)
        )

        tree.selection_set(rows[0])
        tree.event_generate("<<TreeviewSelect>>")
        root.update()
        assert goods.get() == "тетрадь"
        goods.delete(0, "end")
        goods.insert(0, "ручка")
        next(item for item in widgets if _text(item) == "Изменить").invoke()
        assert tree.item(tree.get_children()[0], "values")[1] == "ручка"

        tree.selection_set(tree.get_children()[0])
        next(item for item in widgets if _text(item) == "Удалить").invoke()
        assert tree.get_children() == ()

        color = next(item for item in widgets if _text(item) == "Сменить цвет")
        color.invoke()
        swatch = next(item for item in widgets if item.winfo_class() == "Label")
        assert swatch.cget("bg") == "#2255aa"

        click = next(item for item in widgets if _text(item) == "Клик")
        click.invoke()
        assert any("счёт 1" in _text(item) for item in _descendants(root))
        next(item for item in widgets if _text(item) == "Сброс").invoke()
        assert any("счёт 0" in _text(item) for item in _descendants(root))
        assert (tmp_path / "best.txt").read_text(encoding="utf-8").strip() == "1"
    finally:
        if shelf is not None and root.winfo_exists():
            root.destroy()
        if shelf is not None:
            assert shelf.conn is None


def test_headless_cli() -> None:
    env = os.environ.copy()
    env["MTP_HEADLESS"] = "1"
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "калькулятор" in result.stdout

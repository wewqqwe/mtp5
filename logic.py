"""Логика окна варианта 3, без виджетов."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def calculate(left: float, op: str, right: float) -> float:
    """Четыре действия. Деление на ноль — ZeroDivisionError."""
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        if right == 0:
            raise ZeroDivisionError("деление на ноль")
        return left / right
    raise ValueError(op)


TAB_BODIES = {
    "формулы": "Справка: операции калькулятора + − × ÷",
    "журнал": "Журнал пуст — действий ещё не было",
}


def tab_titles() -> list[str]:
    return list(TAB_BODIES)


def tab_body(title: str) -> str:
    return TAB_BODIES[title]


class ColorBoard:
    def __init__(self) -> None:
        self.current = "#dddddd"

    def apply(self, color: str) -> str:
        self.current = color
        return self.current


class Clicker:
    def __init__(self) -> None:
        self.score = 0

    def click(self) -> int:
        self.score += 1
        return self.score


class SqliteShelf:
    """Слой данных для GUI SQLite: таблица goods."""

    def __init__(self, path: str | Path) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS goods ("
            "id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        self.conn.commit()

    def add(self, name: str) -> int:
        cur = self.conn.execute("INSERT INTO goods (name) VALUES (?)", (name,))
        self.conn.commit()
        return int(cur.lastrowid)

    def get(self, row_id: int) -> dict[str, int | str] | None:
        row = self.conn.execute(
            "SELECT id, name FROM goods WHERE id = ?", (row_id,)
        ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1]}

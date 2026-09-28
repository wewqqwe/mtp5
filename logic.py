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


def parse_operands(left_raw: str, op: str, right_raw: str) -> tuple[float, str, float]:
    """Числа из полей. Запятая — десятичный разделитель. Пустое поле — ValueError."""
    left = float(left_raw.strip().replace(",", "."))
    right = float(right_raw.strip().replace(",", "."))
    return left, op.strip(), right


def present_result(left_raw: str, op: str, right_raw: str) -> str:
    """Текст метки калькулятора. Ошибки ввода наружу не выходят."""
    try:
        left, sign, right = parse_operands(left_raw, op, right_raw)
        return str(calculate(left, sign, right))
    except ZeroDivisionError:
        return "ошибка: деление на ноль"
    except ValueError:
        return "ошибка: нужны числа и операция + - * /"


TAB_BODIES = {
    "формулы": "Справка: операции калькулятора + − × ÷",
    "журнал": "Журнал пуст — действий ещё не было",
}


def tab_titles() -> list[str]:
    return list(TAB_BODIES)


def tab_body(title: str) -> str:
    return TAB_BODIES[title]


class ActionLog:
    """Журнал успешных операций калькулятора."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def record(self, line: str) -> str:
        self.lines.append(line)
        return self.text()

    def text(self) -> str:
        if not self.lines:
            return TAB_BODIES["журнал"]
        return "\n".join(self.lines[-8:])


class ColorBoard:
    def __init__(self) -> None:
        self.current = "#dddddd"

    def apply(self, color: str) -> str:
        self.current = color
        return self.current


class Clicker:
    """Раунд на время: клики, цель, уровень, рекорд, автоклик."""

    def __init__(
        self,
        round_seconds: int = 15,
        best_path: str | Path | None = None,
    ) -> None:
        self.score = 0
        self.best = 0
        self.level = 1
        self.goal = 10
        self.round_seconds = round_seconds
        self.seconds_left = round_seconds
        self.running = False
        self.auto = False
        self.best_path = Path(best_path) if best_path is not None else None
        if self.best_path is not None:
            self.load_best()

    def click(self) -> int:
        self.score += 1
        if self.score > self.best:
            self.best = self.score
            self._write_best()
        if self.score >= self.goal:
            self.level += 1
            self.goal += 5
        return self.score

    def reset(self) -> int:
        self.score = 0
        self.seconds_left = self.round_seconds
        self.running = False
        return self.score

    def toggle_auto(self) -> bool:
        self.auto = not self.auto
        return self.auto

    def start_round(self) -> int:
        self.score = 0
        self.seconds_left = self.round_seconds
        self.running = True
        return self.seconds_left

    def tick(self) -> int:
        """Одна секунда раунда. Вне раунда секунды не меняет."""
        if not self.running:
            return self.seconds_left
        if self.auto:
            self.click()
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self.seconds_left = 0
            self.running = False
        return self.seconds_left

    def status(self) -> str:
        if self.running:
            phase = "раунд идёт"
        elif self.seconds_left == 0:
            phase = "раунд окончен"
        else:
            phase = "ожидание"
        auto = "вкл" if self.auto else "выкл"
        return (
            f"счёт {self.score} | рекорд {self.best} | "
            f"уровень {self.level} | цель {self.goal} | "
            f"{self.seconds_left} с | {phase} | авто {auto}"
        )

    def load_best(self, path: str | Path | None = None) -> int:
        file = Path(path) if path is not None else self.best_path
        if file is None or not file.exists():
            return self.best
        text = file.read_text(encoding="utf-8").strip()
        if text.isdigit():
            self.best = max(self.best, int(text))
        if path is not None:
            self.best_path = file
        return self.best

    def save_best(self, path: str | Path | None = None) -> None:
        file = Path(path) if path is not None else self.best_path
        if file is None:
            raise ValueError("нет пути для рекорда")
        self.best_path = file
        self._write_best()

    def _write_best(self) -> None:
        if self.best_path is None:
            return
        self.best_path.write_text(f"{self.best}\n", encoding="utf-8")


class SqliteShelf:
    """Слой данных для GUI SQLite: таблица goods."""

    def __init__(self, path: str | Path) -> None:
        self.conn: sqlite3.Connection | None = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS goods ("
            "id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        self.conn.commit()

    def add(self, name: str) -> int:
        clean = name.strip()
        if not clean:
            raise ValueError("пустое название")
        cur = self._conn().execute(
            "INSERT INTO goods (name) VALUES (?)", (clean,)
        )
        self._conn().commit()
        return cur.lastrowid or 0

    def get(self, row_id: int) -> dict[str, int | str] | None:
        row = self._conn().execute(
            "SELECT id, name FROM goods WHERE id = ?", (row_id,)
        ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1]}

    def list(self) -> list[dict[str, int | str]]:
        rows = self._conn().execute(
            "SELECT id, name FROM goods ORDER BY id"
        ).fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]

    def update(self, row_id: int, name: str) -> bool:
        clean = name.strip()
        if not clean:
            raise ValueError("пустое название")
        cur = self._conn().execute(
            "UPDATE goods SET name = ? WHERE id = ?", (clean, row_id)
        )
        self._conn().commit()
        return cur.rowcount > 0

    def delete(self, row_id: int) -> bool:
        cur = self._conn().execute("DELETE FROM goods WHERE id = ?", (row_id,))
        self._conn().commit()
        return cur.rowcount > 0

    def close(self) -> None:
        if self.conn is None:
            return
        self.conn.close()
        self.conn = None

    def _conn(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError("соединение закрыто")
        return self.conn

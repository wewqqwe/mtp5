from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from logic import (
    Clicker,
    ColorBoard,
    SqliteShelf,
    calculate,
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


def test_sqlite_shelf(tmp_path: Path) -> None:
    shelf = SqliteShelf(tmp_path / "goods.db")
    row_id = shelf.add("тетрадь")
    loaded = shelf.get(row_id)
    assert loaded is not None
    assert loaded["name"] == "тетрадь"
    raw = sqlite3.connect(tmp_path / "goods.db")
    assert raw.execute("SELECT name FROM goods").fetchone()[0] == "тетрадь"


def test_ui_source_declares_widgets() -> None:
    source = (ROOT / "ui.py").read_text(encoding="utf-8")
    for needle in ("ttk.Notebook", "Button", "nb.add", "Clicker", "SqliteShelf", "calculate"):
        assert needle in source


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

"""Блок E1 · eval. Первое, что должно работать: ничего не крутить без цифры.

Контракт: docs/contracts/E1_eval.md. Владелец: Арсений.
Запуск: uv run python -m app.blocks.eval [--golden data/fixture/golden.jsonl] [--hidden] [--judge]
"""

from __future__ import annotations

from pathlib import Path

from app.blocks.eval.l0 import evaluate as _evaluate
from app.blocks.eval.l0 import format_table as _format_table
from app.blocks.eval.l0 import load_golden as _load_golden
from app.contracts.models import EvalResult, GoldenItem


def load_golden(path: Path, hidden: bool | None = None) -> list[GoldenItem]:
    """jsonl → GoldenItem. hidden=True → только hidden, False → только open, None → все."""
    return _load_golden(path, hidden=hidden)


def evaluate(items: list[GoldenItem], judge: bool = False) -> EvalResult:
    """Прогнать W1.ask по каждому элементу, посчитать N/M по метрикам и по категориям."""
    return _evaluate(items, judge=judge)


def format_table(result: EvalResult) -> str:
    """Таблица для терминала и слайда: метрика | N/M. Без процентов."""
    return _format_table(result)


__all__ = ["evaluate", "format_table", "load_golden"]

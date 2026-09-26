"""Блок E1 · eval. Первое, что должно работать: ничего не крутить без цифры.

Контракт: docs/contracts/E1_eval.md. Владелец: Арсений.
Запуск: uv run python -m app.blocks.eval [--golden data/fixture/golden.jsonl] [--hidden] [--judge]
"""

from __future__ import annotations

from pathlib import Path

from app.contracts.models import EvalResult, GoldenItem


def load_golden(path: Path, hidden: bool | None = None) -> list[GoldenItem]:
    """jsonl → GoldenItem. hidden=True → только hidden, False → только open, None → все."""
    raise NotImplementedError("E1")


def evaluate(items: list[GoldenItem], judge: bool = False) -> EvalResult:
    """Прогнать W1.ask по каждому элементу, посчитать N/M по метрикам и по категориям."""
    raise NotImplementedError("E1")


def format_table(result: EvalResult) -> str:
    """Таблица для терминала и слайда: метрика | N/M. Без процентов."""
    raise NotImplementedError("E1")

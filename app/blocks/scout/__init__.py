"""Блок S1 · scout. Офлайн-поиск конфликтов между источниками. Запускается один раз после индексации.

Контракт: docs/contracts/S1_scout.md. Владелец: Никита, запасной Арсений.
L0 (SCOUT=manual): regex-префильтр + ручные пары из data/fixture/conflicts.json / data/conflicts_manual.json.
L1 (SCOUT=llm): группы ≥ 2 chunks с одной сущностью → фронтир-судья через app.blocks.llm.complete_json.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from app.contracts.models import Chunk, Conflict


class EntityGroup(BaseModel):
    """Chunks, в которых regex нашёл одну и ту же сущность (тариф, часы, срок, телефон, номер решения)."""

    key: str  # "<category>|<entity_kind>|<keyword>", например "mobility|tariff|troleibuz"
    entity_kind: str  # tariff | hours | deadline | phone | decision | address
    chunk_ids: list[str]


def prefilter(chunks: list[Chunk]) -> list[EntityGroup]:
    """Regex: числа + lei/MDL, ore/часы HH:MM, zile/дней, телефоны, nr. решений.

    Только группы из ≥ 2 chunks.
    """
    raise NotImplementedError("S1")


def load_manual(path: Path) -> list[Conflict]:
    """Ручные пары от дизайнеров (G1). Формат — data/fixture/conflicts.json."""
    raise NotImplementedError("S1")


def judge(group: EntityGroup, chunks: list[Chunk]) -> list[Conflict]:
    """L1. Одна группа → 0..N конфликтов через LLM. Ошибка/None от модели → []."""
    raise NotImplementedError("S1")


def run(chunks: list[Chunk], manual_path: Path | None = None) -> list[Conflict]:
    """Порт: manual + (при SCOUT=llm) judge по группам. Детерминированный порядок, без дублей по (a,b)."""
    raise NotImplementedError("S1")

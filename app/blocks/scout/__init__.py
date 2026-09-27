"""Блок S1 · scout. Офлайн-поиск конфликтов между источниками. Запускается один раз после индексации.

Контракт: docs/contracts/S1_scout.md. Владелец: Никита, запасной Арсений.
L0 (SCOUT=manual): regex-префильтр + ручные пары из data/fixture/conflicts.json / data/conflicts_manual.json.
L1 (SCOUT=llm): группы ≥ 2 chunks с одной сущностью → фронтир-судья через app.blocks.llm.complete_json.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel

from app.config import ROOT, settings
from app.contracts.models import Chunk, Conflict

log = logging.getLogger(__name__)


class EntityGroup(BaseModel):
    """Chunks, в которых regex нашёл одну и ту же сущность (тариф, часы, срок, телефон, номер решения)."""

    key: str  # "<category>|<entity_kind>|<keyword>", например "mobility|tariff|troleibuz"
    entity_kind: str  # tariff | hours | deadline | phone | decision | address
    chunk_ids: list[str]


def prefilter(chunks: list[Chunk]) -> list[EntityGroup]:
    """Regex: числа + lei/MDL, ore/часы HH:MM, zile/дней, телефоны, nr. решений.

    Только группы из ≥ 2 chunks.
    """
    from app.blocks.scout import l0

    return l0.prefilter(chunks)


def load_manual(path: Path) -> list[Conflict]:
    """Ручные пары от дизайнеров (G1). Формат — data/fixture/conflicts.json."""
    from app.blocks.scout import l0

    return l0.load_manual(path)


def judge(group: EntityGroup, chunks: list[Chunk]) -> list[Conflict]:
    """При SCOUT=llm судит через LLM-порт; ошибка пропускает группу."""
    if settings.SCOUT != "llm":
        return []
    from app.blocks.scout import l1

    try:
        return l1.judge(group, chunks)
    except Exception:
        log.warning("S1 judge failed for group %s; skipping it", group.key, exc_info=True)
        return []


def run(chunks: list[Chunk], manual_path: Path | None = None) -> list[Conflict]:
    """Запускает ручной источник и, при SCOUT=llm, судью по regex-группам."""
    from app.blocks.scout import l0

    selected_path = manual_path
    if selected_path is None:
        default_path = ROOT / "data" / "conflicts_manual.json"
        selected_path = default_path if default_path.exists() else settings.FIXTURE_DIR / "conflicts.json"
    conflicts = l0.load_manual(selected_path)
    if settings.SCOUT == "llm":
        for group in prefilter(chunks):
            conflicts.extend(judge(group, chunks))

    unique = l0.deduplicate(conflicts)
    unique.sort(
        key=lambda conflict: (
            conflict.a.citation.chunk_id,
            conflict.b.citation.chunk_id,
            conflict.id,
        )
    )
    return unique


def seed_startup_conflicts() -> int:
    """Засев ручных конфликтов при старте приложения (settings.SEED_CONFLICTS=1).

    Нужен, потому что в fixture-режиме БД — in-memory на процесс (см. app.blocks.store):
    без внутрипроцессного вызова scout конфликты видит только офлайн `python -m app.blocks.scout`,
    запущенный СНАРУЖИ, что не работает для in-memory БД сервера. idempotent: insert_conflict
    делает UPSERT по id, повторный вызов не дублирует записи.
    CORPUS=fixture → data/fixture/conflicts.json. CORPUS=real → data/conflicts_manual.json, если есть.
    """
    from app.blocks import store

    if not settings.SEED_CONFLICTS:
        return 0

    if settings.CORPUS == "fixture":
        manual_path = settings.FIXTURE_DIR / "conflicts.json"
    else:
        manual_path = ROOT / "data" / "conflicts_manual.json"
        if not manual_path.exists():
            return 0

    conn = store.connect()
    try:
        conflicts = load_manual(manual_path)
        for conflict in conflicts:
            store.insert_conflict(conn, conflict)
        return len(conflicts)
    finally:
        conn.close()

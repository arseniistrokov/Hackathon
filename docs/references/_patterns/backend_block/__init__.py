"""Блок <ID> · <Название>. Порт блока — только функции, объявленные здесь.

Контракт: docs/contracts/<ID>_example.md. Реализация: l0.py (без сети), l1.py (целевой уровень).
Файл создан каркасом C0: тела функций заменяются, сигнатуры — нет.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.contracts.models import Passage, Query

from . import l0

log = logging.getLogger(__name__)


def rerank(query: Query, passages: list[Passage], k: int | None = None) -> list[Passage]:
    """Единая точка входа. Уровень выбирается переключателем из контракта (здесь — RERANKER)."""
    k = k or settings.TOP_K
    if settings.RERANKER == "lexical":
        return l0.rerank(query, passages, k)
    try:
        from . import l1  # тяжёлые зависимости — только когда уровень включён

        return l1.rerank(query, passages, k)
    except Exception:  # noqa: BLE001 — любая ошибка L1 = тихий откат на L0, не падение
        log.warning("<ID>: L1 failed, falling back to L0", exc_info=True)
        return l0.rerank(query, passages, k)


def is_enough(passages: list[Passage]) -> bool:
    return bool(passages) and passages[0].score >= settings.RERANK_THRESHOLD

"""Блок R2 · rerank. Это и есть механизм NOT_FOUND: скор reranker'а — единственная калибруемая цифра.

Контракт: docs/contracts/R2_rerank.md. Владелец: Арсений.
RERANKER=lexical → нормированное перекрытие токенов без диакритики (L0).
RERANKER=bge     → CrossEncoder BAAI/bge-reranker-v2-m3 (extra ml, L1); ошибка → откат на lexical.
"""

from __future__ import annotations

from app.contracts.models import Passage, Query


def rerank(query: Query, passages: list[Passage], k: int | None = None) -> list[Passage]:
    """top-K (settings.TOP_K) с score 0..1 по убыванию, перенумерованные n=1..K."""
    raise NotImplementedError("R2")


def is_enough(passages: list[Passage]) -> bool:
    """True, если лучший score ≥ settings.RERANK_THRESHOLD. Пустой список → False."""
    raise NotImplementedError("R2")

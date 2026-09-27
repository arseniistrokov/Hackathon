"""Блок R2 · rerank. Это и есть механизм NOT_FOUND: скор reranker'а — единственная калибруемая цифра.

Контракт: docs/contracts/R2_rerank.md. Владелец: Арсений.
RERANKER=lexical → нормированное перекрытие токенов без диакритики (L0).
RERANKER=bge     → CrossEncoder BAAI/bge-reranker-v2-m3 (extra ml, L1); ошибка → откат на lexical.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.contracts.models import Passage, Query

from . import l0

log = logging.getLogger(__name__)


def rerank(query: Query, passages: list[Passage], k: int | None = None) -> list[Passage]:
    """top-K (settings.TOP_K) с score 0..1 по убыванию, перенумерованные n=1..K."""
    top_k = k or settings.TOP_K
    if settings.RERANKER != "bge":
        return l0.rerank(query, passages, top_k)
    try:
        from . import l1

        return l1.rerank(query, passages, top_k)
    except Exception:  # noqa: BLE001 — любая ошибка L1 = откат на lexical, не падение
        log.warning("R2: bge reranker failed, falling back to lexical", exc_info=True)
        return l0.rerank(query, passages, top_k)


def is_enough(passages: list[Passage], query: Query | None = None) -> bool:
    """True, если лучший score ≥ settings.RERANK_THRESHOLD. Пустой список → False.

    `query` необязателен (обратная совместимость контракта R2, старые вызовы без него не меняют
    поведение): если передан — доп. фильтр против мусорных вопросов не по теме корпуса, у которых
    высокий score получается на 1 случайном общем слове (напр. "Cine a câștigat campionatul
    mondial?" против чужого passage о "campionat" в другом контексте). Требуем ≥2 общих значимых
    (после l0.normalize) токенов top-1 vs текста вопроса — минимальное ужесточение вместо смены
    порога (единый порог не отделяет весь мусор от демо-вопросов на реальном индексе).
    """
    if not passages or passages[0].score < settings.RERANK_THRESHOLD:
        return False
    if query is None:
        return True
    query_tokens = set(l0.normalize(query.search_text)) | set(l0.normalize(query.text))
    passage_tokens = set(l0.normalize(passages[0].chunk.text))
    return len(query_tokens & passage_tokens) >= 2

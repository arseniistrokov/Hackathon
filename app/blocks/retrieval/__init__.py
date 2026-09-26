"""Блок R1 · retrieval. Гибридный поиск: FTS5 (D1) + косинус по numpy-матрице → RRF → top-N.

Контракт: docs/contracts/R1_retrieval.md. Владелец: Арсений.
EMBEDDER=hash   → детерминированные char-ngram эмбеддинги (без модели, L0).
EMBEDDER=bge-m3 → sentence-transformers BAAI/bge-m3 (extra ml, L1); ошибка → откат на hash.
"""

from __future__ import annotations

import numpy as np

from app.contracts.models import Lang, Passage, Query


def make_query(text: str, lang: Lang | None = None) -> Query:
    """detect_lang (L1) → для ru: search_text = translate(text, 'ro').

    Категория — если роутер уверен, иначе None.
    """
    raise NotImplementedError("R1")


def embed(texts: list[str]) -> np.ndarray:
    """float32 [len(texts), dim], L2-нормировано. Одинаковые тексты → одинаковые векторы."""
    raise NotImplementedError("R1")


def retrieve(query: Query, n: int | None = None) -> list[Passage]:
    """top-N кандидатов (settings.TOP_N) с RRF-скором и sources. Нумерация n=1.. по убыванию скора."""
    raise NotImplementedError("R1")


def build_index() -> int:
    """Посчитать эмбеддинги для всех chunks из D1 и сохранить через D1.save_embeddings.

    Вернуть число строк.
    """
    raise NotImplementedError("R1")

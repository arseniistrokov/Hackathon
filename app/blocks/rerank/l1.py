"""L1: целевая реализация. Тяжёлые импорты — внутри функции, чтобы L0 работал без extra ml.

Ошибки НЕ ловим здесь: их ловит порт в __init__.py и откатывается на L0.
"""

from __future__ import annotations

from functools import lru_cache

from app.contracts.models import Passage, Query


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import CrossEncoder  # extra ml; загружается один раз на процесс

    return CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)


def rerank(query: Query, passages: list[Passage], k: int) -> list[Passage]:
    if not passages:
        return []

    import numpy as np

    scores = _model().predict([(query.search_text, p.chunk.text) for p in passages], activation_fn=None)
    probs = 1 / (1 + np.exp(-np.asarray(scores, dtype="float32")))
    order = sorted(range(len(passages)), key=lambda i: (-float(probs[i]), passages[i].n))
    return [
        passages[i].model_copy(update={"n": rank, "score": float(probs[i])})
        for rank, i in enumerate(order[:k], 1)
    ]

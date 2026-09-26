"""L1: bge-m3 эмбеддинги. Тяжёлые импорты — только здесь и лениво. Ошибки не ловим — их ловит порт."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

_DIM = 1024


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer  # extra ml; загружается один раз на процесс

    return SentenceTransformer("BAAI/bge-m3")


def embed(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, _DIM), dtype=np.float32)
    vectors = _model().encode(texts, batch_size=32, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)

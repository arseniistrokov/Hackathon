"""L0: детерминированные эмбеддинги (char-ngram hashing) и словарь-детектор категории. Без сети и моделей."""

from __future__ import annotations

import hashlib
import unicodedata

import numpy as np

_DIM = 2048
_NGRAM = 3

# Ключевые слова — уже без диакритики и в нижнем регистре (сравниваются с folded-текстом).
_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "transparency": ("petit", "decizi", "regulament"),
    "mobility": ("troleibuz", "autobuz", "abonament"),
    "urban": ("salubriz", "deseuri", "gunoi"),
    "education": ("gradinit", "elev", "tineret"),
    "health": ("medic", "vaccin", "policlinic"),
    "districts": ("pretur", "audien", "sector"),
    "services": ("cerere", "formular", "serviciu"),
}


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _tokens(text: str) -> list[str]:
    padded = f"#{_fold(text)}#"
    if len(padded) <= _NGRAM:
        return [padded]
    return [padded[i : i + _NGRAM] for i in range(len(padded) - _NGRAM + 1)]


def _bucket(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % _DIM


def embed(texts: list[str]) -> np.ndarray:
    matrix = np.zeros((len(texts), _DIM), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in _tokens(text):
            matrix[row, _bucket(token)] += 1.0
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return (matrix / np.where(norms == 0, 1, norms)).astype(np.float32, copy=False)


def detect_category(text: str) -> str | None:
    """≥ 2 совпадения одной категории и 0 совпадений остальных → эта категория, иначе None."""
    folded = _fold(text)
    counts = {
        category: sum(folded.count(keyword) for keyword in keywords)
        for category, keywords in _CATEGORY_KEYWORDS.items()
    }
    matched = {category: count for category, count in counts.items() if count > 0}
    if len(matched) != 1:
        return None
    ((category, count),) = matched.items()
    return category if count >= 2 else None

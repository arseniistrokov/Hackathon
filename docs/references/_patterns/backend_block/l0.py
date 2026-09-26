"""L0: детерминированно, без сети, без моделей, без ключей. Одни данные → один и тот же результат."""

from __future__ import annotations

import unicodedata

from app.contracts.models import Passage, Query

_STOP = {"de", "la", "în", "și", "a", "cu", "pe", "care", "este", "и", "в", "на", "с", "по", "как", "что"}


def normalize(text: str) -> list[str]:
    """Нижний регистр, диакритика снята (ș→s, ț→t, ă→a), стоп-слова убраны. Только для сравнения, не для цитат."""
    text = text.lower().replace("ș", "s").replace("ş", "s").replace("ț", "t").replace("ţ", "t")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return [t for t in "".join(c if c.isalnum() else " " for c in text).split() if t not in _STOP]


def rerank(query: Query, passages: list[Passage], k: int) -> list[Passage]:
    q = set(normalize(query.search_text)) | set(normalize(query.text))
    if not q:
        return []
    scored = []
    for p in passages:
        overlap = len(q & set(normalize(p.chunk.text))) / len(q)
        scored.append((overlap, p.n, p))
    scored.sort(key=lambda t: (-t[0], t[1]))  # стабильно: при равных — исходный порядок
    return [p.model_copy(update={"n": i, "score": round(s, 4)}) for i, (s, _, p) in enumerate(scored[:k], 1)]

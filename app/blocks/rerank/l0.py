"""L0: детерминированно, без сети, без моделей, без ключей. Одни данные → один и тот же результат."""

from __future__ import annotations

import unicodedata

from app.contracts.models import Passage, Query

_STOP = {"de", "la", "în", "și", "a", "cu", "pe", "care", "este", "и", "в", "на", "с", "по", "как", "что"}
_STEM_LEN = 6  # усечение до префикса: ro/ru — суффиксальные языки (petiției/petiționarului/petițiile)


def normalize(text: str) -> list[str]:
    """Нижний регистр, диакритика снята (ș→s, ț→t, ă→a), стоп-слова убраны, токен усечён до префикса.

    Усечение — суррогат стемминга: без него точное совпадение токенов почти никогда не срабатывает
    на ro/ru словоформах одного корня (петиция/петиции/петиционера), включая fixture-критерий 1.
    Только для сравнения скора, не для цитат.
    """
    text = text.lower().replace("ș", "s").replace("ş", "s").replace("ț", "t").replace("ţ", "t")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    tokens = "".join(c if c.isalnum() else " " for c in text).split()
    return [t[:_STEM_LEN] for t in tokens if t not in _STOP]


def _overlap(query_tokens: set[str], passage_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens & passage_tokens) / len(query_tokens)


def rerank(query: Query, passages: list[Passage], k: int) -> list[Passage]:
    """score = max(overlap(search_text, passage), overlap(text, passage)) — контракт требует оба, не union."""
    if not passages:
        return []
    search_tokens = set(normalize(query.search_text))
    text_tokens = set(normalize(query.text))

    scored = []
    for p in passages:
        passage_tokens = set(normalize(p.chunk.text))
        score = max(_overlap(search_tokens, passage_tokens), _overlap(text_tokens, passage_tokens))
        scored.append((score, p.n, p))
    scored.sort(key=lambda t: (-t[0], t[1]))  # стабильно: при равных — исходный порядок n
    return [p.model_copy(update={"n": i, "score": round(s, 4)}) for i, (s, _, p) in enumerate(scored[:k], 1)]

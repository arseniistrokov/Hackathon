"""Блок W1 · workflow. Детерминированный проход: одна функция, фиксированный порядок шагов, без графов.

Контракт: docs/contracts/W1_workflow.md. Владелец: Арсений.
make_query → retrieve → rerank → evidence gate (CONFLICT | NOT_FOUND | ENOUGH)
→ generate → verify → AskResponse.
Модель цитаты не пишет: она выбирает номера passages, passage берётся из базы по id.
"""

from __future__ import annotations

from app.contracts.models import AskResponse, Lang, LLMAnswer, Passage


def ask(question: str, lang: Lang | None = None) -> AskResponse:
    """Единая точка входа для POST /api/ask и eval.py."""
    raise NotImplementedError("W1")


def verify_citations(answer: LLMAnswer, passages: list[Passage]) -> list[Passage]:
    """Оставить только номера из retrieved-набора, без дублей, в порядке из answer. Пусто → NOT_FOUND."""
    raise NotImplementedError("W1")


def extractive_answer(passages: list[Passage], lang: Lang) -> LLMAnswer:
    """L0 без модели: ответ = текст лучшего passage, citations=[1], enough=True."""
    raise NotImplementedError("W1")

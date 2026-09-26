"""Блок L1 · llm. ЕДИНСТВЕННОЕ место в проекте, которое ходит в модель.

Контракт: docs/contracts/L1_llm.md. Владелец: Арсений.
LLM=off  → complete_json возвращает None, translate — идентичность, detect_lang — эвристика по кириллице.
LLM=ollama → /api/chat с format=<json schema>, think=false, temperature 0.1.
LLM=api  → OpenAI-совместимый endpoint с response_format json_schema (fallback на демо).
Любая ошибка (сеть, таймаут, невалидный JSON) → None или исходный текст. Наружу исключения не летят.
Внешний текст (passages, вопрос) — данные в `user`, никогда в `system`.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.contracts.models import Lang


def complete_json[T: BaseModel](
    system: str, user: str, schema: type[T], timeout_s: float | None = None
) -> T | None:
    """Ответ модели строго по pydantic-схеме или None."""
    raise NotImplementedError("L1")


def translate(text: str, target: Lang) -> str:
    """Короткий перевод вопроса (ru→ro для поиска). Ошибка или LLM=off → text без изменений."""
    raise NotImplementedError("L1")


def detect_lang(text: str) -> Lang:
    """Кириллица ≥ 30% букв → ru, иначе ro. Без модели."""
    raise NotImplementedError("L1")


def model_name() -> str:
    """"extractive" при LLM=off, иначе имя модели — в meta.model и в feedback."""
    raise NotImplementedError("L1")

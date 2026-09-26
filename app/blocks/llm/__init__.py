"""Блок L1 · llm. ЕДИНСТВЕННОЕ место в проекте, которое ходит в модель.

Контракт: docs/contracts/L1_llm.md. Владелец: Арсений.
LLM=off  → complete_json возвращает None, translate — идентичность, detect_lang — эвристика по кириллице.
LLM=ollama → /api/chat с format=<json schema>, think=false, temperature 0.1.
LLM=api  → OpenAI-совместимый endpoint с response_format json_schema (fallback на демо).
Любая ошибка (сеть, таймаут, невалидный JSON) → None или исходный текст. Наружу исключения не летят.
Внешний текст (passages, вопрос) — данные в `user`, никогда в `system`.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel

from app.config import settings
from app.contracts.models import Lang

from . import l0

log = logging.getLogger(__name__)


def complete_json[T: BaseModel](
    system: str, user: str, schema: type[T], timeout_s: float | None = None
) -> T | None:
    """Ответ модели строго по pydantic-схеме или None."""
    if settings.LLM not in ("ollama", "api"):
        return l0.complete_json(system, user, schema, timeout_s)
    try:
        from . import l1

        if settings.LLM == "ollama":
            return l1.complete_json_ollama(system, user, schema, timeout_s)
        return l1.complete_json_api(system, user, schema, timeout_s)
    except Exception:  # noqa: BLE001 — любая ошибка L1 = None, не падение
        log.warning("L1: complete_json failed, falling back to None", exc_info=True)
        return None


def translate(text: str, target: Lang) -> str:
    """Короткий перевод вопроса (ru→ro для поиска). Ошибка или LLM=off → text без изменений."""
    if settings.LLM not in ("ollama", "api") or not text.strip():
        return l0.translate(text, target)
    try:
        from . import l1

        return l1.translate(text, target)
    except Exception:  # noqa: BLE001 — любая ошибка L1 = исходный текст, не падение
        log.warning("L1: translate failed, falling back to source text", exc_info=True)
        return text


def detect_lang(text: str) -> Lang:
    """Кириллица ≥ 30% букв → ru, иначе ro. Без модели."""
    return l0.detect_lang(text)


def model_name() -> str:
    """ "extractive" при LLM=off, иначе OLLAMA_MODEL / API_MODEL — в meta.model и в feedback."""
    if settings.LLM == "ollama":
        return settings.OLLAMA_MODEL
    if settings.LLM == "api":
        return settings.API_MODEL
    return "extractive"

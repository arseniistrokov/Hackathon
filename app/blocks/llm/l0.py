"""L0: без сети, без моделей, без ключей. Детерминировано."""

from __future__ import annotations

from pydantic import BaseModel

from app.contracts.models import Lang

_CYRILLIC = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


def complete_json(system: str, user: str, schema: type[BaseModel], timeout_s: float | None = None) -> None:
    return None


def translate(text: str, target: Lang) -> str:
    return text


def detect_lang(text: str) -> Lang:
    """Кириллица ≥ 30% букв → ru, иначе ro; пустая строка → ro."""
    letters = [c for c in text.lower() if c.isalpha()]
    if not letters:
        return "ro"
    cyrillic = sum(1 for c in letters if c in _CYRILLIC)
    return "ru" if cyrillic / len(letters) >= 0.3 else "ro"

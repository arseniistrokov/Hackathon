"""Блок I2 · chunker. Чистая функция, без сети и без уровней.

Контракт: docs/contracts/I2_chunker.md. Владелец: Никита.
"""

from __future__ import annotations

from app.contracts.models import Chunk, RawPage


def chunk(page: RawPage, target: int = 600, overlap: int = 90) -> list[Chunk]:
    """Разбить страницу по заголовкам → абзацам на chunks ~target символов с overlap. Детерминировано."""
    raise NotImplementedError("I2")


def chunk_id(url: str, section: str | None, ordinal: int) -> str:
    """sha1(f'{url}|{section or ""}|{ordinal}')[:16]."""
    raise NotImplementedError("I2")


def document_id(url: str) -> str:
    """sha1(url)[:16]."""
    raise NotImplementedError("I2")

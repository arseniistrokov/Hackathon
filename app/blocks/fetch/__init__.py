"""Блок I1 · fetch. Порт блока — только функции, объявленные здесь.

Контракт: docs/contracts/I1_fetch.md. Владелец: Никита.
L0: load_raw() читает data/fixture/mini_corpus (без сети).
L1: сеть — sitemap / WP REST / httpx+trafilatura / PDF.
Файл создан каркасом C0: тела функций заменяются, сигнатуры — нет.
"""

from __future__ import annotations

from pathlib import Path

from app.contracts.models import RawPage


def load_raw(root: Path) -> list[RawPage]:
    """Прочитать сохранённые страницы: <root>/<site>/<slug>.md + <slug>.meta.json. Без сети."""
    raise NotImplementedError("I1")


def save_raw(page: RawPage, root: Path) -> Path:
    """Сохранить страницу в <root>/<site>/<slug>.md + .meta.json; вернуть путь к .md. Идемпотентно."""
    raise NotImplementedError("I1")


def list_urls(site: str, limit: int = 150) -> list[str]:
    """L1. Кандидаты URL сайта: sitemap.xml → WP REST (/wp-json/wp/v2/pages, /posts) → BFS same-domain."""
    raise NotImplementedError("I1")


def fetch_page(url: str, site: str) -> RawPage | None:
    """L1. httpx (timeout 10 c, 1 повтор) + trafilatura (или WP REST json, или pymupdf для PDF).

    Мусор → None.
    """
    raise NotImplementedError("I1")

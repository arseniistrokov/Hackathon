"""Блок D1 · store. SQLite (documents, chunks, chunks_fts, conflicts, feedback, queries, site_pages) + .npy.

Контракт: docs/contracts/D1_store.md. Владелец: Никита.
L0: CORPUS=fixture → база в памяти из data/fixture/mini_corpus. L1: CORPUS=real → файл DB_PATH.
Единственное место в проекте, где есть SQL. Векторная БД не нужна: эмбеддинги — numpy-матрица в .npy.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import numpy as np

from app.contracts.models import Chunk, Conflict, Navigation, RawPage, Stats


def connect() -> sqlite3.Connection:
    """Соединение по settings.CORPUS: fixture → :memory: (заполняется один раз), real → DB_PATH.

    Схема создана.
    """
    raise NotImplementedError("D1")


def init_schema(conn: sqlite3.Connection) -> None:
    """CREATE TABLE IF NOT EXISTS … chunks_fts — FTS5 с tokenize='unicode61 remove_diacritics 2'."""
    raise NotImplementedError("D1")


def upsert_document(conn: sqlite3.Connection, page: RawPage, document_id: str) -> None:
    raise NotImplementedError("D1")


def upsert_chunks(conn: sqlite3.Connection, chunks: list[Chunk]) -> int:
    """Вставить/обновить по id; content_hash не изменился → пропустить. Вернуть число новых."""
    raise NotImplementedError("D1")


def get_chunks(conn: sqlite3.Connection, ids: list[str]) -> list[Chunk]:
    """В порядке ids. Неизвестный id пропускается."""
    raise NotImplementedError("D1")


def all_chunk_ids(conn: sqlite3.Connection) -> list[str]:
    """Порядок строк матрицы эмбеддингов = порядок этого списка (стабильно: ORDER BY rowid)."""
    raise NotImplementedError("D1")


def fts_search(
    conn: sqlite3.Connection, query: str, k: int = 20, category: str | None = None
) -> list[tuple[str, float]]:
    """FTS5 MATCH по chunks_fts → [(chunk_id, bm25)], лучшие первыми. Запрос экранируется, OR по словам."""
    raise NotImplementedError("D1")


def save_embeddings(ids: list[str], matrix: np.ndarray, path: Path) -> None:
    """matrix float32 [len(ids), dim], L2-нормирована. Рядом пишется <path>.ids.json."""
    raise NotImplementedError("D1")


def load_embeddings(path: Path) -> tuple[list[str], np.ndarray] | None:
    """None, если файла нет."""
    raise NotImplementedError("D1")


def insert_conflict(conn: sqlite3.Connection, conflict: Conflict) -> None:
    raise NotImplementedError("D1")


def conflicts_for(conn: sqlite3.Connection, chunk_ids: list[str]) -> list[Conflict]:
    """Конфликты, у которых a или b — один из chunk_ids."""
    raise NotImplementedError("D1")


def save_query(conn: sqlite3.Connection, query_id: str, question: str, lang: str, status: str,
               answer: str, chunk_ids: list[str], model: str, latency_ms: int) -> None:
    raise NotImplementedError("D1")


def save_feedback(conn: sqlite3.Connection, query_id: str, rating: int, comment: str) -> None:
    raise NotImplementedError("D1")


def site_navigation(conn: sqlite3.Connection, site: str) -> Navigation | None:
    """Контактная/сервисная страница сайта из data/sites.yaml (таблица site_pages)."""
    raise NotImplementedError("D1")


def stats(conn: sqlite3.Connection) -> Stats:
    raise NotImplementedError("D1")


def document_date(conn: sqlite3.Connection, document_id: str) -> date | None:
    raise NotImplementedError("D1")

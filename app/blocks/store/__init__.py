"""Блок D1 · store. SQLite (documents, chunks, chunks_fts, conflicts, feedback, queries, site_pages) + .npy.

Контракт: docs/contracts/D1_store.md. Владелец: Никита.
L0: CORPUS=fixture → база в памяти из data/fixture/mini_corpus. L1: CORPUS=real → файл DB_PATH.
Единственное место в проекте, где есть SQL. Векторная БД не нужна: эмбеддинги — numpy-матрица в .npy.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from app.config import settings
from app.contracts.models import Chunk, Conflict, Navigation, RawPage, Stats

_fixture_template: sqlite3.Connection | None = None


def connect() -> sqlite3.Connection:
    """Соединение по settings.CORPUS: fixture → :memory: (заполняется один раз), real → DB_PATH.

    Схема создана.
    """
    global _fixture_template
    if settings.CORPUS == "real":
        settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_schema(conn)
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    if _fixture_template is not None:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _fixture_template.backup(conn)
        return conn

    import yaml
    from docs.references._patterns.backend_block import fixture_loader

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    pages = fixture_loader.load_raw(settings.FIXTURE_DIR / "mini_corpus")
    sites = yaml.safe_load(settings.SITES_PATH.read_text(encoding="utf-8"))

    for page in pages:
        document_id = fixture_loader.document_id(page.url)
        conn.execute(
            """INSERT INTO documents
               (id, site, url, title, category, lang, date, kind, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (document_id, page.site, page.url, page.title, page.category, page.lang,
             page.date.isoformat() if page.date else None, page.kind,
             page.fetched_at.isoformat() if page.fetched_at else None),
        )
        for chunk in fixture_loader.chunk(page):
            conn.execute(
                """INSERT INTO chunks
                   (id, document_id, site, category, url, title, section, page,
                    text, lang, date, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chunk.id, chunk.document_id, chunk.site, chunk.category, chunk.url,
                 chunk.title, chunk.section, chunk.page, chunk.text, chunk.lang,
                 chunk.date.isoformat() if chunk.date else None, chunk.content_hash),
            )

    for site, metadata in sites.items():
        conn.execute(
            """INSERT INTO site_pages (site, label, contact, services, url)
               VALUES (?, ?, ?, ?, ?)""",
            (site, metadata.get("label", site), metadata.get("contact"),
             metadata.get("services"), metadata["url"]),
        )
    conn.commit()
    _fixture_template = conn
    instance = sqlite3.connect(":memory:", check_same_thread=False)
    instance.row_factory = sqlite3.Row
    conn.backup(instance)
    return instance


def init_schema(conn: sqlite3.Connection) -> None:
    """Создать таблицы хранилища и синхронизируемый полнотекстовый индекс."""
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, site TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL, category TEXT NOT NULL, lang TEXT NOT NULL,
            date TEXT, kind TEXT NOT NULL, fetched_at TEXT
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY, document_id TEXT NOT NULL, site TEXT NOT NULL,
            category TEXT NOT NULL, url TEXT NOT NULL, title TEXT NOT NULL,
            section TEXT, page INTEGER, text TEXT NOT NULL, lang TEXT NOT NULL,
            date TEXT, content_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conflicts (
            id TEXT PRIMARY KEY, entity TEXT NOT NULL, a_chunk TEXT NOT NULL,
            b_chunk TEXT NOT NULL, a_value TEXT NOT NULL, b_value TEXT NOT NULL,
            a_date TEXT, b_date TEXT, resolved_by_date INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS queries (
            id TEXT PRIMARY KEY, ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            question TEXT NOT NULL, lang TEXT NOT NULL, status TEXT NOT NULL,
            answer TEXT NOT NULL, chunk_ids TEXT NOT NULL, model TEXT NOT NULL,
            latency_ms INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY, query_id TEXT NOT NULL, rating INTEGER NOT NULL,
            comment TEXT NOT NULL DEFAULT '', ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(query_id) REFERENCES queries(id)
        );
        CREATE TABLE IF NOT EXISTS site_pages (
            site TEXT PRIMARY KEY, label TEXT NOT NULL, contact TEXT,
            services TEXT, url TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            text, title, section, content='chunks', content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 2'
        );
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, text, title, section)
            VALUES (new.rowid, new.text, new.title, new.section);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text, title, section)
            VALUES ('delete', old.rowid, old.text, old.title, old.section);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text, title, section)
            VALUES ('delete', old.rowid, old.text, old.title, old.section);
            INSERT INTO chunks_fts(rowid, text, title, section)
            VALUES (new.rowid, new.text, new.title, new.section);
        END;
        """
    )


def upsert_document(conn: sqlite3.Connection, page: RawPage, document_id: str) -> None:
    conn.execute(
        """INSERT INTO documents
           (id, site, url, title, category, lang, date, kind, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             site=excluded.site, url=excluded.url, title=excluded.title,
             category=excluded.category, lang=excluded.lang, date=excluded.date,
             kind=excluded.kind, fetched_at=excluded.fetched_at""",
        (document_id, page.site, page.url, page.title, page.category, page.lang,
         page.date.isoformat() if page.date else None, page.kind,
         page.fetched_at.isoformat() if page.fetched_at else None),
    )


def upsert_chunks(conn: sqlite3.Connection, chunks: list[Chunk]) -> int:
    """Вставить/обновить по id; content_hash не изменился → пропустить. Вернуть число новых."""
    inserted = 0
    for chunk in chunks:
        row = conn.execute("SELECT content_hash FROM chunks WHERE id = ?", (chunk.id,)).fetchone()
        if row is not None and row[0] == chunk.content_hash:
            continue
        values = (
            chunk.document_id, chunk.site, chunk.category, chunk.url, chunk.title,
            chunk.section, chunk.page, chunk.text, chunk.lang,
            chunk.date.isoformat() if chunk.date else None, chunk.content_hash,
        )
        if row is None:
            conn.execute(
                """INSERT INTO chunks
                   (id, document_id, site, category, url, title, section, page,
                    text, lang, date, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chunk.id, *values),
            )
            inserted += 1
        else:
            conn.execute(
                """UPDATE chunks SET document_id=?, site=?, category=?, url=?,
                   title=?, section=?, page=?, text=?, lang=?, date=?, content_hash=?
                   WHERE id=?""",
                (*values, chunk.id),
            )
    conn.commit()
    return inserted


def get_chunks(conn: sqlite3.Connection, ids: list[str]) -> list[Chunk]:
    """В порядке ids. Неизвестный id пропускается."""
    if not ids:
        return []
    placeholders = ",".join("?" for _ in set(ids))
    rows = conn.execute(
        f"SELECT * FROM chunks WHERE id IN ({placeholders})", tuple(dict.fromkeys(ids))
    ).fetchall()
    by_id = {row["id"]: Chunk.model_validate(dict(row)) for row in rows}
    return [by_id[chunk_id] for chunk_id in ids if chunk_id in by_id]


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

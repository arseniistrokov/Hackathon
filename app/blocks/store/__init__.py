"""Блок D1 · store. SQLite (documents, chunks, chunks_fts, conflicts, feedback, queries, site_pages) + .npy.

Контракт: docs/contracts/D1_store.md. Владелец: Никита.
L0: CORPUS=fixture → база в памяти из data/fixture/mini_corpus. L1: CORPUS=real → файл DB_PATH.
Единственное место в проекте, где есть SQL. Векторная БД не нужна: эмбеддинги — numpy-матрица в .npy.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from app.config import settings
from app.contracts.models import Chunk, Citation, Conflict, ConflictSide, Navigation, RawPage, Stats

_fixture_template: sqlite3.Connection | None = None
log = logging.getLogger(__name__)


def connect() -> sqlite3.Connection:
    """Соединение по settings.CORPUS: fixture → :memory: (заполняется один раз), real → DB_PATH.

    Схема создана.
    """
    if settings.CORPUS == "real":
        conn: sqlite3.Connection | None = None
        try:
            settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            init_schema(conn)
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        except Exception as exc:
            if conn is not None:
                conn.close()
            log.warning("CORPUS=real unavailable; falling back to fixture: %s", exc)
            return _connect_fixture()

    return _connect_fixture()


def _connect_fixture() -> sqlite3.Connection:
    global _fixture_template

    if _fixture_template is not None:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _fixture_template.backup(conn)
        return conn

    import yaml

    from app.blocks import chunker, fetch

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    pages = fetch.load_raw(settings.FIXTURE_DIR / "mini_corpus")
    sites = yaml.safe_load(settings.SITES_PATH.read_text(encoding="utf-8"))

    for page in pages:
        document_id = chunker.document_id(page.url)
        conn.execute(
            """INSERT INTO documents
               (id, site, url, title, category, lang, date, kind, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                document_id,
                page.site,
                page.url,
                page.title,
                page.category,
                page.lang,
                page.date.isoformat() if page.date else None,
                page.kind,
                page.fetched_at.isoformat() if page.fetched_at else None,
            ),
        )
        for chunk in chunker.chunk(page):
            conn.execute(
                """INSERT INTO chunks
                   (id, document_id, site, category, url, title, section, page,
                    text, lang, date, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    chunk.id,
                    chunk.document_id,
                    chunk.site,
                    chunk.category,
                    chunk.url,
                    chunk.title,
                    chunk.section,
                    chunk.page,
                    chunk.text,
                    chunk.lang,
                    chunk.date.isoformat() if chunk.date else None,
                    chunk.content_hash,
                ),
            )

    for site, metadata in sites.items():
        conn.execute(
            """INSERT INTO site_pages (site, label, contact, services, url)
               VALUES (?, ?, ?, ?, ?)""",
            (
                site,
                metadata.get("label", site),
                metadata.get("contact"),
                metadata.get("services"),
                metadata["url"],
            ),
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
        (
            document_id,
            page.site,
            page.url,
            page.title,
            page.category,
            page.lang,
            page.date.isoformat() if page.date else None,
            page.kind,
            page.fetched_at.isoformat() if page.fetched_at else None,
        ),
    )
    conn.commit()


def upsert_chunks(conn: sqlite3.Connection, chunks: list[Chunk]) -> int:
    """Вставить/обновить по id; content_hash не изменился → пропустить. Вернуть число новых."""
    inserted = 0
    for chunk in chunks:
        row = conn.execute("SELECT content_hash FROM chunks WHERE id = ?", (chunk.id,)).fetchone()
        if row is not None and row[0] == chunk.content_hash:
            continue
        values = (
            chunk.document_id,
            chunk.site,
            chunk.category,
            chunk.url,
            chunk.title,
            chunk.section,
            chunk.page,
            chunk.text,
            chunk.lang,
            chunk.date.isoformat() if chunk.date else None,
            chunk.content_hash,
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
    return [row[0] for row in conn.execute("SELECT id FROM chunks ORDER BY rowid").fetchall()]


def fts_search(
    conn: sqlite3.Connection, query: str, k: int = 20, category: str | None = None
) -> list[tuple[str, float]]:
    """FTS5 MATCH по chunks_fts → [(chunk_id, bm25)], лучшие первыми. Запрос экранируется, OR по словам."""
    if k <= 0:
        return []
    words = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
    if not words:
        return []
    match_query = " OR ".join(f'"{word}"' for word in words)
    rows = conn.execute(
        """SELECT chunks.id, bm25(chunks_fts) AS score
           FROM chunks_fts
           JOIN chunks ON chunks.rowid = chunks_fts.rowid
           WHERE chunks_fts MATCH ? AND (? IS NULL OR chunks.category = ?)
           ORDER BY score ASC, chunks.rowid ASC LIMIT ?""",
        (match_query, category, category, k),
    ).fetchall()
    return [(row[0], float(row[1])) for row in rows]


def save_embeddings(ids: list[str], matrix: np.ndarray, path: Path) -> None:
    """matrix float32 [len(ids), dim], L2-нормирована. Рядом пишется <path>.ids.json."""
    import numpy as np

    values = np.asarray(matrix, dtype=np.float32)
    if values.ndim != 2 or values.shape[0] != len(ids):
        raise ValueError("matrix must have shape [len(ids), dim]")
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    normalized = values / np.where(norms == 0, 1, norms)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, normalized.astype(np.float32, copy=False), allow_pickle=False)
    ids_path = Path(f"{path}.ids.json")
    ids_path.write_text(json.dumps(ids, ensure_ascii=False) + "\n", encoding="utf-8")


def load_embeddings(path: Path) -> tuple[list[str], np.ndarray] | None:
    """None, если файла нет."""
    import numpy as np

    ids_path = Path(f"{path}.ids.json")
    if not path.is_file() or not ids_path.is_file():
        return None
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    matrix = np.load(path, allow_pickle=False).astype(np.float32, copy=False)
    if matrix.ndim != 2 or matrix.shape[0] != len(ids):
        raise ValueError("embedding ids do not match matrix rows")
    return ids, matrix


def insert_conflict(conn: sqlite3.Connection, conflict: Conflict) -> None:
    conn.execute(
        """INSERT INTO conflicts
           (id, entity, a_chunk, b_chunk, a_value, b_value, a_date, b_date, resolved_by_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET entity=excluded.entity, a_chunk=excluded.a_chunk,
             b_chunk=excluded.b_chunk, a_value=excluded.a_value, b_value=excluded.b_value,
             a_date=excluded.a_date, b_date=excluded.b_date,
             resolved_by_date=excluded.resolved_by_date""",
        (
            conflict.id,
            conflict.entity,
            conflict.a.citation.chunk_id,
            conflict.b.citation.chunk_id,
            conflict.a.value,
            conflict.b.value,
            conflict.a.date.isoformat() if conflict.a.date else None,
            conflict.b.date.isoformat() if conflict.b.date else None,
            int(conflict.resolved_by_date),
        ),
    )
    conn.commit()


def conflicts_for(conn: sqlite3.Connection, chunk_ids: list[str]) -> list[Conflict]:
    """Конфликты, у которых a или b — один из chunk_ids."""
    if not chunk_ids:
        return []
    unique_ids = list(dict.fromkeys(chunk_ids))
    placeholders = ",".join("?" for _ in unique_ids)
    rows = conn.execute(
        f"SELECT * FROM conflicts WHERE a_chunk IN ({placeholders}) "
        f"OR b_chunk IN ({placeholders}) ORDER BY id",
        (*unique_ids, *unique_ids),
    ).fetchall()
    chunks = {
        chunk.id: chunk
        for chunk in get_chunks(conn, [value for row in rows for value in (row["a_chunk"], row["b_chunk"])])
    }
    conflicts: list[Conflict] = []
    for row in rows:
        a_chunk = chunks.get(row["a_chunk"])
        b_chunk = chunks.get(row["b_chunk"])
        if a_chunk is None or b_chunk is None:
            continue
        conflicts.append(
            Conflict(
                id=row["id"],
                entity=row["entity"],
                a=ConflictSide(
                    citation=_citation(a_chunk),
                    value=row["a_value"],
                    date=date.fromisoformat(row["a_date"]) if row["a_date"] else None,
                ),
                b=ConflictSide(
                    citation=_citation(b_chunk),
                    value=row["b_value"],
                    date=date.fromisoformat(row["b_date"]) if row["b_date"] else None,
                ),
                resolved_by_date=bool(row["resolved_by_date"]),
            )
        )
    return conflicts


def save_query(
    conn: sqlite3.Connection,
    query_id: str,
    question: str,
    lang: str,
    status: str,
    answer: str,
    chunk_ids: list[str],
    model: str,
    latency_ms: int,
) -> None:
    conn.execute(
        """INSERT INTO queries (id, question, lang, status, answer, chunk_ids, model, latency_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET question=excluded.question, lang=excluded.lang,
             status=excluded.status, answer=excluded.answer, chunk_ids=excluded.chunk_ids,
             model=excluded.model, latency_ms=excluded.latency_ms""",
        (
            query_id,
            question,
            lang,
            status,
            answer,
            json.dumps(chunk_ids, ensure_ascii=False),
            model,
            latency_ms,
        ),
    )
    conn.commit()


def save_feedback(conn: sqlite3.Connection, query_id: str, rating: int, comment: str) -> None:
    conn.execute(
        "INSERT INTO feedback (query_id, rating, comment) VALUES (?, ?, ?)",
        (query_id, rating, comment),
    )
    conn.commit()


def site_navigation(conn: sqlite3.Connection, site: str) -> Navigation | None:
    """Контактная/сервисная страница сайта из data/sites.yaml (таблица site_pages)."""
    row = conn.execute(
        "SELECT label, contact, services, url FROM site_pages WHERE site = ?", (site,)
    ).fetchone()
    if row is None:
        return None
    return Navigation(label=row["label"], url=row["contact"] or row["services"] or row["url"])


def stats(conn: sqlite3.Connection) -> Stats:
    documents, chunks, sites, conflicts, queries, feedback_up, feedback_down = conn.execute(
        """SELECT
             (SELECT COUNT(*) FROM documents),
             (SELECT COUNT(*) FROM chunks),
             (SELECT COUNT(DISTINCT site) FROM documents),
             (SELECT COUNT(*) FROM conflicts),
             (SELECT COUNT(*) FROM queries),
             (SELECT COUNT(*) FROM feedback WHERE rating = 1),
             (SELECT COUNT(*) FROM feedback WHERE rating = -1)"""
    ).fetchone()
    return Stats(
        corpus_documents=documents,
        corpus_chunks=chunks,
        sites=sites,
        conflicts=conflicts,
        queries=queries,
        feedback_up=feedback_up,
        feedback_down=feedback_down,
        model="extractive",
    )


def document_date(conn: sqlite3.Connection, document_id: str) -> date | None:
    row = conn.execute("SELECT date FROM documents WHERE id = ?", (document_id,)).fetchone()
    return date.fromisoformat(row[0]) if row and row[0] else None


def _citation(chunk: Chunk) -> Citation:
    return Citation(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        title=chunk.title,
        url=chunk.url,
        site=chunk.site,
        section=chunk.section,
        page=chunk.page,
        passage=chunk.text,
        date=chunk.date,
    )

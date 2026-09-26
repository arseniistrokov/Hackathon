"""PII-маска перед записью в SQLite и retention (EU alignment C1/C3). Без сети, без моделей."""

from __future__ import annotations

import sqlite3

import app.blocks.store as store
import pytest
from app.contracts.models import Stats


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = store.connect()
    store.init_schema(c)
    return c


def test_redact_pii_masks_idnp_email_and_phone() -> None:
    text = "Sunt Ion, IDNP 1234567890123, e-mail ion@example.md, tel +373 69 123 456"
    redacted = store._redact_pii(text)
    assert "1234567890123" not in redacted
    assert "ion@example.md" not in redacted
    assert "69 123 456" not in redacted
    assert redacted.count("[REDACTED]") == 3


def test_redact_pii_leaves_ordinary_text_untouched() -> None:
    text = "Care este tariful la troleibuz?"
    assert store._redact_pii(text) == text


def test_save_query_masks_question_before_storing(conn: sqlite3.Connection) -> None:
    store.save_query(
        conn,
        query_id="qid_pii_1",
        question="Numele meu e Maria, IDNP 9876543210123",
        lang="ro",
        status="ANSWERED",
        answer="Costul este de 6 lei.",
        chunk_ids=[],
        model="extractive",
        latency_ms=1,
    )
    row = conn.execute("SELECT question FROM queries WHERE id = ?", ("qid_pii_1",)).fetchone()
    assert "9876543210123" not in row["question"]
    assert "[REDACTED]" in row["question"]


def test_save_feedback_masks_comment_before_storing(conn: sqlite3.Connection) -> None:
    store.save_query(
        conn,
        query_id="qid_pii_2",
        question="Care este programul?",
        lang="ro",
        status="ANSWERED",
        answer="...",
        chunk_ids=[],
        model="extractive",
        latency_ms=1,
    )
    store.save_feedback(conn, query_id="qid_pii_2", rating=1, comment="Scrieți-mi la test@exemplu.md")
    row = conn.execute("SELECT comment FROM feedback WHERE query_id = ?", ("qid_pii_2",)).fetchone()
    assert "test@exemplu.md" not in row["comment"]
    assert "[REDACTED]" in row["comment"]


def test_purge_old_queries_removes_only_expired_rows(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO queries (id, ts, question, lang, status, answer, chunk_ids, model, latency_ms) "
        "VALUES ('old', datetime('now', '-40 days'), 'q', 'ro', 'ANSWERED', 'a', '[]', 'extractive', 1)"
    )
    conn.execute(
        "INSERT INTO queries (id, ts, question, lang, status, answer, chunk_ids, model, latency_ms) "
        "VALUES ('new', datetime('now'), 'q', 'ro', 'ANSWERED', 'a', '[]', 'extractive', 1)"
    )
    conn.execute("INSERT INTO feedback (query_id, rating, comment) VALUES ('old', 1, '')")
    conn.commit()

    removed = store.purge_old_queries(conn, days=30)

    assert removed == 1
    remaining_ids = {row[0] for row in conn.execute("SELECT id FROM queries").fetchall()}
    assert remaining_ids == {"new"}
    assert conn.execute("SELECT COUNT(*) FROM feedback WHERE query_id = 'old'").fetchone()[0] == 0


def test_purge_old_queries_keeps_stats_consistent(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO queries (id, ts, question, lang, status, answer, chunk_ids, model, latency_ms) "
        "VALUES ('old', datetime('now', '-31 days'), 'q', 'ro', 'ANSWERED', 'a', '[]', 'extractive', 1)"
    )
    conn.commit()

    store.purge_old_queries(conn, days=30)

    s: Stats = store.stats(conn)
    assert s.queries == 0

"""Тесты приёмки блока D1 · store. Один тест = один критерий приёмки.

Запуск: uv run pytest tests/blocks/store/test_acceptance.py -q
На момент написания реализация — NotImplementedError, все тесты красные.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date
from pathlib import Path

import app.blocks.store as store
import pytest
from app.config import settings
from app.contracts.models import (
    Chunk,
    Citation,
    Conflict,
    ConflictSide,
    Navigation,
    RawPage,
    Stats,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(
    n: int,
    *,
    site: str = "rtec.md",
    category: str = "mobility",
    url: str = "https://rtec.md/tarife-calatorie",
    text: str = "Costul unei călătorii în troleibuz este de 6 lei.",
    section: str | None = None,
) -> Chunk:
    """Construct a deterministic Chunk for tests."""
    cid = hashlib.sha1(f"{url}|{section or ''}|{n}".encode()).hexdigest()[:16]
    doc_id = hashlib.sha1(url.encode()).hexdigest()[:16]
    content_hash = hashlib.sha1(text.encode()).hexdigest()[:16]
    return Chunk(
        id=cid,
        document_id=doc_id,
        site=site,
        category=category,
        url=url,
        title="Tarife călătorie",
        section=section,
        text=text,
        lang="ro",
        date=None,
        content_hash=content_hash,
    )


def _make_citation(chunk: Chunk) -> Citation:
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


def _make_conflict(a_chunk: Chunk, b_chunk: Chunk) -> Conflict:
    return Conflict(
        id="cf_test_001",
        entity="tarif călătorie troleibuz",
        a=ConflictSide(citation=_make_citation(a_chunk), value="6 lei", date=date(2024, 7, 1)),
        b=ConflictSide(citation=_make_citation(b_chunk), value="2 lei", date=date(2021, 3, 10)),
        resolved_by_date=True,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def expect() -> dict:
    """Load the canonical expected-values fixture."""
    return json.loads((settings.FIXTURE_DIR / "expect.json").read_text(encoding="utf-8"))


@pytest.fixture
def conn() -> sqlite3.Connection:
    """Fresh in-memory connection with schema initialised before each test."""
    c = store.connect()
    store.init_schema(c)
    return c


def test_init_schema_creates_tables_and_is_idempotent() -> None:
    """D1-2: схема содержит контрактные таблицы и повторно создаётся без ошибок."""
    c = sqlite3.connect(":memory:")
    store.init_schema(c)
    store.init_schema(c)

    names = {row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}
    assert {"documents", "chunks", "chunks_fts", "conflicts", "queries", "feedback", "site_pages"} <= names
    sql = c.execute("SELECT sql FROM sqlite_master WHERE name = 'chunks_fts'").fetchone()[0]
    assert "unicode61 remove_diacritics 2" in sql


def test_connect_fixture_loads_corpus_once(expect: dict) -> None:
    """D1: fixture connection has a schema and loads the canonical corpus."""
    c = store.connect()
    document_count = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    chunk_count = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    site_count = c.execute("SELECT COUNT(DISTINCT site) FROM documents").fetchone()[0]

    assert document_count == expect["documents"]
    assert chunk_count >= document_count * expect["min_chunks_per_page"]
    assert site_count == expect["sites"]
    second = store.connect()
    assert second is not c
    assert second.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == document_count


def test_real_storage_error_logs_and_falls_back_to_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, expect: dict
) -> None:
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(settings, "CORPUS", "real")
    monkeypatch.setattr(settings, "DB_PATH", blocked_parent / "index.sqlite")

    with caplog.at_level("WARNING", logger="app.blocks.store"):
        conn = store.connect()

    assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == expect["documents"]
    assert "falling back to fixture" in caplog.text


def test_upsert_document_inserts_and_updates() -> None:
    """Документ сохраняется и повторный upsert обновляет его метаданные."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    store.init_schema(c)
    page = RawPage(
        site="rtec.md",
        url="https://example.test/page",
        title="Titlu vechi",
        text="Text de fixture suficient pentru a construi pagina.",
        category="mobility",
    )
    store.upsert_document(c, page, "doc_manual")
    updated = page.model_copy(update={"title": "Titlu nou"})
    store.upsert_document(c, updated, "doc_manual")

    rows = c.execute("SELECT id, title FROM documents").fetchall()
    assert [tuple(row) for row in rows] == [("doc_manual", "Titlu nou")]


# ---------------------------------------------------------------------------
# Критерий 1 — статистика корпуса fixture
# ---------------------------------------------------------------------------


def test_stats_on_fixture(expect: dict) -> None:
    """Критерий 1: connect() на fixture даёт ожидаемое число документов, чанков и сайтов."""
    c = store.connect()
    store.init_schema(c)
    s: Stats = store.stats(c)

    assert s.corpus_documents == expect["documents"], (
        f"corpus_documents={s.corpus_documents}, ожидалось {expect['documents']}"
    )
    assert s.corpus_chunks >= expect["documents"] * expect["min_chunks_per_page"], (
        f"corpus_chunks={s.corpus_chunks} < documents×min_chunks_per_page"
    )
    assert s.sites == expect["sites"], f"sites={s.sites}, ожидалось {expect['sites']}"


# ---------------------------------------------------------------------------
# Критерий 2 — FTS без диакритики
# ---------------------------------------------------------------------------


def test_fts_search_diacritics_insensitive(conn: sqlite3.Connection, expect: dict) -> None:
    """Критерий 2: 'petitie termen' и 'petiție termen' оба находят целевой passage в top-3."""
    target_passage = expect["petition_term_passage"]

    for query_text in ("petitie termen", "petiție termen"):
        results = store.fts_search(conn, query_text, k=20)
        assert results, f"fts_search({query_text!r}) вернул пустой список"

        top3_ids = [chunk_id for chunk_id, _ in results[:3]]
        chunks = store.get_chunks(conn, top3_ids)
        found = any(target_passage in ch.text for ch in chunks)
        assert found, (
            f"fts_search({query_text!r}): passage {target_passage!r} не найден в top-3; top-3 ids={top3_ids}"
        )


# ---------------------------------------------------------------------------
# Критерий 3 — фильтрация по категории
# ---------------------------------------------------------------------------


def test_fts_search_category_filter(conn: sqlite3.Connection) -> None:
    """Критерий 3: fts_search с category='mobility' возвращает только chunks с category=='mobility'."""
    results = store.fts_search(conn, "troleibuz tarif", k=20, category="mobility")
    assert isinstance(results, list)

    if results:
        ids = [chunk_id for chunk_id, _ in results]
        chunks = store.get_chunks(conn, ids)
        for ch in chunks:
            assert ch.category == "mobility", (
                f"Chunk {ch.id} имеет category={ch.category!r}, ожидалось 'mobility'"
            )


# ---------------------------------------------------------------------------
# Критерий 4 — спецсимволы и пустая строка не бросают
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query_text",
    [
        'Ordinea "publică"',
        "tarif*",
        "troleibuz AND tarif",
        '"',
        "",
    ],
)
def test_fts_search_special_chars_and_empty(conn: sqlite3.Connection, query_text: str) -> None:
    """Критерий 4: специальные символы FTS и пустая строка не бросают исключений; пустая строка → []."""
    result = store.fts_search(conn, query_text)
    assert isinstance(result, list), f"fts_search({query_text!r}) вернул не список"
    if query_text == "":
        assert result == [], f"fts_search('') должен возвращать [], вернул {result}"


# ---------------------------------------------------------------------------
# Критерий 5 — идемпотентность upsert_chunks
# ---------------------------------------------------------------------------


def test_upsert_chunks_idempotent(conn: sqlite3.Connection) -> None:
    """Критерий 5: второй upsert тех же чанков возвращает 0 и не увеличивает число строк."""
    chunks = [
        _make_chunk(
            0,
            url="https://rtec.md/upsert-test",
            text="Costul unei călătorii în troleibuz este de 6 lei.",
        ),
        _make_chunk(
            1,
            url="https://rtec.md/upsert-test",
            text="Abonamentul lunar costă 60 de lei pentru toate rutele.",
        ),
    ]

    first = store.upsert_chunks(conn, chunks)
    assert first == len(chunks), f"Первый upsert вернул {first}, ожидалось {len(chunks)}"

    count_before: int = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    second = store.upsert_chunks(conn, chunks)
    count_after: int = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    assert second == 0, f"Второй upsert вернул {second}, ожидалось 0"
    assert count_after == count_before, f"Число строк выросло: {count_before} → {count_after}"


# ---------------------------------------------------------------------------
# Критерий 6 — порядок get_chunks и пропуск неизвестных id
# ---------------------------------------------------------------------------


def test_get_chunks_order_and_unknown_ids(conn: sqlite3.Connection) -> None:
    """Критерий 6: get_chunks возвращает чанки в порядке запроса; неизвестные id пропускаются."""
    c0 = _make_chunk(0, text="Текст нулевого чанка для теста порядка.")
    c1 = _make_chunk(1, text="Текст первого чанка для теста порядка.")
    store.upsert_chunks(conn, [c0, c1])

    # запрашиваем в обратном порядке + несуществующий id
    result = store.get_chunks(conn, [c1.id, "nonexistent_id_abc123", c0.id])

    assert len(result) == 2, f"Ожидалось 2 чанка, получено {len(result)}"
    assert result[0].id == c1.id, f"Первым должен быть {c1.id}, получен {result[0].id}"
    assert result[1].id == c0.id, f"Вторым должен быть {c0.id}, получен {result[1].id}"


def test_all_chunk_ids_and_document_date_are_stable(conn: sqlite3.Connection) -> None:
    expected_ids = [row[0] for row in conn.execute("SELECT id FROM chunks ORDER BY rowid")]
    assert store.all_chunk_ids(conn) == expected_ids

    dated = conn.execute(
        "SELECT id, date FROM documents WHERE date IS NOT NULL ORDER BY id LIMIT 1"
    ).fetchone()
    undated = conn.execute("SELECT id FROM documents WHERE date IS NULL ORDER BY id LIMIT 1").fetchone()
    assert dated is not None and undated is not None
    assert store.document_date(conn, dated[0]) == date.fromisoformat(dated[1])
    assert store.document_date(conn, undated[0]) is None
    assert store.document_date(conn, "unknown-document") is None


# ---------------------------------------------------------------------------
# Критерий 7 — round-trip эмбеддингов
# ---------------------------------------------------------------------------


def test_embeddings_roundtrip(tmp_path: Path) -> None:
    """Критерий 7: save_embeddings + load_embeddings дают те же ids и ту же матрицу float32."""
    # pytest.importorskip handles the numpy DLL-load failure that occurs when the
    # project path contains a semicolon (Windows PATH separator), which corrupts
    # the DLL search path.  Once the environment is fixed, this skip disappears.
    np = pytest.importorskip("numpy", reason="numpy DLL не загружается (путь содержит ';')")

    ids = ["aaaa", "bbbb", "cccc"]
    matrix = np.random.randn(3, 8).astype(np.float32)
    # L2-нормируем вручную (как должна делать реализация)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix = (matrix / np.where(norms == 0, 1, norms)).astype(np.float32)

    emb_path = tmp_path / "embeddings.npy"
    store.save_embeddings(ids, matrix, emb_path)

    loaded = store.load_embeddings(emb_path)
    assert loaded is not None, "load_embeddings вернул None"

    loaded_ids, loaded_matrix = loaded
    assert loaded_ids == ids, f"ids после round-trip не совпадают: {loaded_ids} != {ids}"
    assert loaded_matrix.dtype == np.float32, (
        f"dtype после загрузки: {loaded_matrix.dtype}, ожидалось float32"
    )
    np.testing.assert_array_almost_equal(
        loaded_matrix, matrix, decimal=6, err_msg="Матрица эмбеддингов изменилась после round-trip"
    )


# ---------------------------------------------------------------------------
# Критерий 8 — конфликты
# ---------------------------------------------------------------------------


def test_conflicts_for(conn: sqlite3.Connection) -> None:
    """Критерий 8: insert_conflict + conflicts_for по a_chunk и b_chunk; [] на пустом списке."""
    a_chunk = _make_chunk(
        10,
        url="https://rtec.md/tarife-calatorie",
        text="Costul unei călătorii în troleibuz este de 6 lei.",
    )
    b_chunk = _make_chunk(
        20,
        site="chisinau.md",
        category="transparency",
        url="https://www.chisinau.md/ro/transport-public-tarife",
        text="costul unei călătorii în troleibuz constituie 2 lei.",
    )
    store.upsert_chunks(conn, [a_chunk, b_chunk])

    conflict = _make_conflict(a_chunk, b_chunk)
    store.insert_conflict(conn, conflict)

    # поиск по a_chunk
    found_a = store.conflicts_for(conn, [a_chunk.id])
    assert any(cf.id == conflict.id for cf in found_a), (
        f"conflicts_for([a_chunk]) не нашёл конфликт {conflict.id}"
    )

    # поиск по b_chunk
    found_b = store.conflicts_for(conn, [b_chunk.id])
    assert any(cf.id == conflict.id for cf in found_b), (
        f"conflicts_for([b_chunk]) не нашёл конфликт {conflict.id}"
    )

    # пустой список → []
    empty = store.conflicts_for(conn, [])
    assert empty == [], f"conflicts_for([]) должен вернуть [], вернул {empty}"


# ---------------------------------------------------------------------------
# Критерий 9 — навигация по сайту
# ---------------------------------------------------------------------------


def test_site_navigation(conn: sqlite3.Connection, expect: dict) -> None:
    """Критерий 9: навигация для известных сайтов и None для неизвестного."""
    # autosalubritate.md — есть в expect.navigation
    nav = store.site_navigation(conn, "autosalubritate.md")
    assert nav is not None, "site_navigation('autosalubritate.md') вернул None"
    assert isinstance(nav, Navigation)
    expected = expect["navigation"]["autosalubritate.md"]
    assert nav.label == expected["label"], f"label={nav.label!r}, ожидалось {expected['label']!r}"
    assert nav.url == expected["url"], f"url={nav.url!r}, ожидалось {expected['url']!r}"

    # сайт без contact/services — должен вернуть url из sites.yaml
    nav_no_contact = store.site_navigation(conn, "rtec.md")
    assert nav_no_contact is not None, (
        "site_navigation('rtec.md') вернул None, ожидался Navigation с url из sites.yaml"
    )
    assert nav_no_contact.url, "url навигации для 'rtec.md' пуст"

    # неизвестный сайт → None
    assert store.site_navigation(conn, "totally-unknown-site.md") is None, (
        "site_navigation с неизвестным сайтом должен вернуть None"
    )


# ---------------------------------------------------------------------------
# Критерий 10 — статистика запросов и обратной связи
# ---------------------------------------------------------------------------


def test_query_feedback_stats(conn: sqlite3.Connection) -> None:
    """Критерий 10: save_query + save_feedback → stats() показывает queries==1, feedback_up==1."""
    query_id = "qid_test_0001"
    store.save_query(
        conn,
        query_id=query_id,
        question="Care este tariful la troleibuz?",
        lang="ro",
        status="ANSWERED",
        answer="Costul este de 6 lei.",
        chunk_ids=["abc", "def"],
        model="extractive",
        latency_ms=42,
    )
    store.save_feedback(conn, query_id=query_id, rating=1, comment="Mulțumesc!")

    s: Stats = store.stats(conn)
    assert s.queries == 1, f"queries={s.queries}, ожидалось 1"
    assert s.feedback_up == 1, f"feedback_up={s.feedback_up}, ожидалось 1"
    assert s.feedback_down == 0, f"feedback_down={s.feedback_down}, ожидалось 0"

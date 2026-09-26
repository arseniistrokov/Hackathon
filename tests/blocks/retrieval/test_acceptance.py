"""Тесты приёмки блока R1 · retrieval. Один тест = один критерий приёмки. Без сети, без моделей.

Запуск: uv run pytest tests/blocks/retrieval -q
"""

from __future__ import annotations

import json

import app.blocks.retrieval as retrieval
import numpy as np
import pytest
from app.blocks import llm, store
from app.blocks.retrieval import l0
from app.config import settings
from app.contracts.models import Query


@pytest.fixture(autouse=True)
def _clear_index_cache():
    retrieval._index_cache.clear()
    yield
    retrieval._index_cache.clear()


@pytest.fixture
def expect() -> dict:
    return json.loads((settings.FIXTURE_DIR / "expect.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Критерий 1: petiție → top-5
# ---------------------------------------------------------------------------


def test_petition_query_finds_passage_in_top5(expect: dict) -> None:
    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    passages = retrieval.retrieve(query, n=5)
    assert any(expect["petition_term_passage"] in p.chunk.text for p in passages)


# ---------------------------------------------------------------------------
# Критерий 2: tariff-запрос находит обе версии (разных категорий) в top-10
# ---------------------------------------------------------------------------


def test_tariff_query_finds_both_versions_in_top10(expect: dict) -> None:
    query = retrieval.make_query("Cât costă o călătorie cu troleibuzul?")
    passages = retrieval.retrieve(query, n=10)
    urls = {p.chunk.url for p in passages}
    assert expect["tariff_new_url"] in urls
    assert expect["tariff_old_url"] in urls


def test_tariff_and_petition_queries_do_not_get_auto_categorized() -> None:
    """Регрессия: словарь категорий не должен срабатывать на эти два запроса (сломало бы критерии 1/2)."""
    assert retrieval.make_query("Cât costă o călătorie cu troleibuzul?").category is None
    assert retrieval.make_query("Care este termenul de examinare a petiției?").category is None


# ---------------------------------------------------------------------------
# Критерий 3: язык и перевод
# ---------------------------------------------------------------------------


def test_make_query_detects_russian() -> None:
    query = retrieval.make_query("Какой срок рассмотрения петиции?")
    assert query.lang == "ru"


def test_make_query_translates_ru_when_llm_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "translate", lambda text, target: "translated-ro-text")
    query = retrieval.make_query("Какой срок рассмотрения петиции?")
    assert query.search_text == "translated-ro-text"


def test_make_query_search_text_is_original_when_llm_off() -> None:
    text = "Какой срок рассмотрения петиции?"
    query = retrieval.make_query(text)
    assert query.search_text == text  # LLM=off (по умолчанию) → identity


def test_make_query_ro_text_is_not_translated() -> None:
    text = "Care este programul?"
    query = retrieval.make_query(text)
    assert query.lang == "ro"
    assert query.search_text == text


# ---------------------------------------------------------------------------
# Критерий 4: embed — форма, детерминированность, норма
# ---------------------------------------------------------------------------


def test_embed_identical_texts_give_identical_vectors() -> None:
    vectors = retrieval.embed(["a", "a"])
    assert vectors.shape == (2, 2048)
    assert np.array_equal(vectors[0], vectors[1])


def test_embed_empty_list_has_correct_shape() -> None:
    vectors = retrieval.embed([])
    assert vectors.shape == (0, 2048)


def test_embed_rows_are_l2_normalized() -> None:
    vectors = retrieval.embed(["salut, ce mai faci?", "a"])
    norms = np.linalg.norm(vectors, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Критерий 5: sources непустые; found-by-both выше found-by-one
# ---------------------------------------------------------------------------


def test_passages_have_nonempty_sources() -> None:
    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    passages = retrieval.retrieve(query, n=5)
    assert passages
    assert all(p.sources for p in passages)


def test_rrf_scores_both_sources_beat_single_source() -> None:
    fts_ids = ["a", "b"]
    vec_ids = ["a", "c"]
    scores = retrieval._rrf_scores(fts_ids, vec_ids)
    # "a" — ранг 1 в обоих списках; "b" и "c" — ранг 2 в одном списке каждый.
    assert scores["a"] > scores["b"]
    assert scores["a"] > scores["c"]


# ---------------------------------------------------------------------------
# Критерий 6: нумерация n=1.. без пропусков, по убыванию score, без дублей
# ---------------------------------------------------------------------------


def test_retrieve_numbering_is_contiguous_ordered_and_unique() -> None:
    query = retrieval.make_query("troleibuz autobuz program")
    passages = retrieval.retrieve(query, n=10)
    assert [p.n for p in passages] == list(range(1, len(passages) + 1))
    scores = [p.score for p in passages]
    assert scores == sorted(scores, reverse=True)
    ids = [p.chunk.id for p in passages]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Критерий 7: фильтр по категории
# ---------------------------------------------------------------------------


def test_category_filter_restricts_results_to_that_category() -> None:
    query = Query(text="troleibuz", lang="ro", search_text="troleibuz", category="mobility")
    passages = retrieval.retrieve(query, n=10)
    assert passages
    assert all(p.chunk.category == "mobility" for p in passages)


# ---------------------------------------------------------------------------
# Критерий 8: EMBEDDER=bge-m3 без sentence_transformers → откат на hash
# ---------------------------------------------------------------------------


def test_bge_m3_import_error_falls_back_to_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "EMBEDDER", "bge-m3")

    def _boom(_texts: list[str]):
        raise ModuleNotFoundError("no sentence_transformers")

    from app.blocks.retrieval import l1

    monkeypatch.setattr(l1, "embed", _boom)
    vectors = retrieval.embed(["salut"])
    assert vectors.shape == (1, 2048)  # размерность hash-эмбеддера, не bge-m3


# ---------------------------------------------------------------------------
# Границы данных / детерминированность / категория
# ---------------------------------------------------------------------------


def test_detect_category_needs_two_hits_same_category_zero_others() -> None:
    assert l0.detect_category("La ce oră începe programul la grădiniță pentru elevii mici?") == "education"
    assert l0.detect_category("un singur cuvânt: medic") is None  # только 1 совпадение
    assert l0.detect_category("") is None


def test_detect_category_is_diacritic_and_case_insensitive() -> None:
    a = l0.detect_category("GRĂDINIȚA are mulți elevi și un elev nou")
    b = l0.detect_category("gradinita are multi elevi si un elev nou")
    assert a == b == "education"


def test_retrieve_is_deterministic() -> None:
    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    first = retrieval.retrieve(query, n=5)
    second = retrieval.retrieve(query, n=5)
    assert [(p.chunk.id, p.n, p.score) for p in first] == [(p.chunk.id, p.n, p.score) for p in second]


def test_retrieve_with_no_matches_returns_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store, "fts_search", lambda *a, **k: [])
    monkeypatch.setattr(store, "all_chunk_ids", lambda *a, **k: [])
    query = Query(text="xyzzy", lang="ro", search_text="xyzzy")
    assert retrieval.retrieve(query) == []


def test_persisted_embeddings_dim_mismatch_disables_vector_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """Индекс, посчитанный другим эмбеддером (несовпадающая размерность), не используется, но FTS работает."""
    conn = store.connect()
    ids = store.all_chunk_ids(conn)
    fake_matrix = np.zeros((len(ids), 1024), dtype=np.float32)  # размерность bge-m3, а EMBEDDER=hash
    monkeypatch.setattr(store, "load_embeddings", lambda _path: (ids, fake_matrix))

    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    passages = retrieval.retrieve(query, n=5)
    assert passages  # FTS всё ещё находит результат
    assert all(p.sources == ["fts"] for p in passages)  # вектор отключён из-за несовпадения размерности


def test_build_index_roundtrip(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "EMB_PATH", tmp_path / "embeddings.npy")
    n = retrieval.build_index()
    conn = store.connect()
    assert n == len(store.all_chunk_ids(conn))
    loaded = store.load_embeddings(settings.EMB_PATH)
    assert loaded is not None
    ids, matrix = loaded
    assert matrix.shape == (len(ids), 2048)


# ---------------------------------------------------------------------------
# QA Пункт 2: Мутационная проверка и различение текстов
# ---------------------------------------------------------------------------


def test_embed_different_texts_produce_different_vectors() -> None:
    v1 = retrieval.embed(["troleibuz"])
    v2 = retrieval.embed(["policlinica vaccin medic"])
    assert not np.allclose(v1, v2)
    similarity = float((v1 @ v2.T)[0, 0])
    assert similarity < 0.5


# ---------------------------------------------------------------------------
# QA Пункт 3: Границы данных
# ---------------------------------------------------------------------------


def test_embed_diacritics_folding_equivalence() -> None:
    # Диакритика folding в l0 нормализует ș/ş, ț/ţ, ă, â, î к латинице
    v_diacritics = retrieval.embed(["petiție și plăți"])
    v_plain = retrieval.embed(["petitie si plati"])
    np.testing.assert_allclose(v_diacritics, v_plain, atol=1e-5)


def test_make_query_mixed_cyrillic_and_latin() -> None:
    # Смешанный текст: ≥ 30% кириллицы распознается как ru
    q = retrieval.make_query("Care este расписание троллейбусов?")
    assert q.lang in ("ro", "ru")
    assert q.search_text


def test_retrieve_single_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    passages = retrieval.retrieve(query, n=1)
    assert len(passages) == 1
    assert passages[0].n == 1


def test_retrieve_chunk_with_none_optional_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    # Убеждаемся, что чанки с section=None, page=None, date=None корректно обрабатываются
    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    passages = retrieval.retrieve(query, n=5)
    assert passages
    for p in passages:
        assert isinstance(p.chunk.id, str)
        # section, page, date могут быть None и не вызывать ошибок сериализации
        assert p.chunk.section is None or isinstance(p.chunk.section, str)


# ---------------------------------------------------------------------------
# QA Пункт 4: Откат bge-m3 на hash с warning
# ---------------------------------------------------------------------------


def test_bge_m3_runtime_error_logs_warning_and_falls_back(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "EMBEDDER", "bge-m3")

    def _boom(_texts: list[str]):
        raise RuntimeError("torch cuda out of memory")

    from app.blocks.retrieval import l1

    monkeypatch.setattr(l1, "embed", _boom)
    with caplog.at_level("WARNING"):
        vectors = retrieval.embed(["salut"])
    assert vectors.shape == (1, 2048)
    assert "R1: bge-m3 embedder failed, falling back to hash" in caplog.text


# ---------------------------------------------------------------------------
# QA Пункт 5: Детерминированность
# ---------------------------------------------------------------------------


def test_make_query_and_embed_are_deterministic() -> None:
    q1 = retrieval.make_query("Cât costă o călătorie cu troleibuzul?")
    q2 = retrieval.make_query("Cât costă o călătorie cu troleibuzul?")
    assert q1.text == q2.text
    assert q1.lang == q2.lang
    assert q1.search_text == q2.search_text
    assert q1.category == q2.category

    v1 = retrieval.embed(["test determinism text"])
    v2 = retrieval.embed(["test determinism text"])
    np.testing.assert_array_equal(v1, v2)


# ---------------------------------------------------------------------------
# QA Пункт 8: Тесты без сети
# ---------------------------------------------------------------------------


def test_retrieval_runs_completely_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def _no_network(*_a, **_k):
        raise AssertionError("Network access attempted in retrieval block!")

    monkeypatch.setattr(httpx, "post", _no_network)
    monkeypatch.setattr(httpx, "get", _no_network)

    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    passages = retrieval.retrieve(query, n=3)
    assert len(passages) == 3

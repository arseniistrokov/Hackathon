"""Тесты приёмки блока R2 · rerank. Один тест = один критерий приёмки. Без сети, без моделей.

Запуск: uv run pytest tests/blocks/rerank -q
"""

from __future__ import annotations

import json

import app.blocks.rerank as rerank
import pytest
from app.blocks import retrieval
from app.blocks.rerank import l0
from app.config import settings
from app.contracts.models import Chunk, Passage, Query


@pytest.fixture(autouse=True)
def _clear_retrieval_index_cache():
    retrieval._index_cache.clear()
    yield
    retrieval._index_cache.clear()


@pytest.fixture
def expect() -> dict:
    return json.loads((settings.FIXTURE_DIR / "expect.json").read_text(encoding="utf-8"))


def _passage(n: int, text: str, url: str = "https://example.md/p", score: float = 0.0) -> Passage:
    chunk = Chunk(
        id=f"c{n:015d}",
        document_id="d" * 16,
        site="rtec.md",
        category="mobility",
        url=url,
        title="t",
        text=text,
        content_hash="h" * 16,
    )
    return Passage(n=n, chunk=chunk, score=score, sources=["fts"])


# ---------------------------------------------------------------------------
# Критерий 1: petiție → первый после rerank, is_enough → True
# ---------------------------------------------------------------------------


def test_petition_passage_ranks_first_and_is_enough(expect: dict) -> None:
    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    candidates = retrieval.retrieve(query, n=10)
    top = rerank.rerank(query, candidates)
    assert expect["petition_term_passage"] in top[0].chunk.text
    assert rerank.is_enough(top)


# ---------------------------------------------------------------------------
# Критерий 2: not_found_queries → is_enough False на дефолтном пороге
# ---------------------------------------------------------------------------


def test_not_found_queries_are_not_enough(expect: dict) -> None:
    for question in expect["not_found_queries"]:
        query = retrieval.make_query(question)
        candidates = retrieval.retrieve(query, n=10)
        top = rerank.rerank(query, candidates)
        assert not rerank.is_enough(top), f"'{question}' неожиданно прошло порог"


# ---------------------------------------------------------------------------
# Критерий 3: границы — ≤K, n=1..K, score невозрастающий, 0<=score<=1, пусто → []
# ---------------------------------------------------------------------------


def test_rerank_respects_k_numbering_and_score_bounds() -> None:
    query = Query(text="troleibuz autobuz program", lang="ro", search_text="troleibuz autobuz program")
    passages = [_passage(i, f"troleibuz autobuz text numarul {i}") for i in range(1, 8)]
    top = rerank.rerank(query, passages, k=3)
    assert len(top) <= 3
    assert [p.n for p in top] == list(range(1, len(top) + 1))
    scores = [p.score for p in top]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_rerank_empty_input_returns_empty_list() -> None:
    query = Query(text="x", lang="ro", search_text="x")
    assert rerank.rerank(query, []) == []


def test_is_enough_empty_list_is_false() -> None:
    assert rerank.is_enough([]) is False


# ---------------------------------------------------------------------------
# Критерий 4: диакритика не меняет lexical-скор
# ---------------------------------------------------------------------------


def test_diacritics_do_not_change_lexical_score() -> None:
    passage_text = "Petițiile se examinează în termen de 30 de zile."
    with_diacritics = rerank.rerank(
        Query(text="petiție termen", lang="ro", search_text="petiție termen"),
        [_passage(1, passage_text)],
    )[0].score
    without_diacritics = rerank.rerank(
        Query(text="petitie termen", lang="ro", search_text="petitie termen"),
        [_passage(1, passage_text)],
    )[0].score
    assert with_diacritics == without_diacritics


# ---------------------------------------------------------------------------
# Критерий 5: стабильность при равных скорах
# ---------------------------------------------------------------------------


def test_rerank_is_deterministic_for_equal_scores() -> None:
    query = Query(text="troleibuz", lang="ro", search_text="troleibuz")
    passages = [_passage(1, "troleibuz text a"), _passage(2, "troleibuz text b")]
    first = rerank.rerank(query, passages)
    second = rerank.rerank(query, passages)
    assert [(p.chunk.id, p.n, p.score) for p in first] == [(p.chunk.id, p.n, p.score) for p in second]


# ---------------------------------------------------------------------------
# Критерий 6: откат RERANKER=bge → lexical при ошибке L1
# ---------------------------------------------------------------------------


def test_bge_exception_falls_back_to_lexical(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RERANKER", "bge")

    from app.blocks.rerank import l1

    def _boom(*_a, **_k):
        raise RuntimeError("model not installed")

    monkeypatch.setattr(l1, "rerank", _boom)

    query = Query(text="petitie termen", lang="ro", search_text="petitie termen")
    passages = [_passage(1, "Petițiile se examinează în termen de 30 de zile.")]
    lexical_only = l0.rerank(query, passages, settings.TOP_K)
    via_port = rerank.rerank(query, passages)
    assert [(p.chunk.id, p.score) for p in via_port] == [(p.chunk.id, p.score) for p in lexical_only]


# ---------------------------------------------------------------------------
# Границы данных
# ---------------------------------------------------------------------------


def test_rerank_handles_duplicate_ids_and_none_optional_fields() -> None:
    chunk = Chunk(
        id="dup",
        document_id="d" * 16,
        site="s",
        category="urban",
        url="https://x.md",
        title="t",
        section=None,
        page=None,
        text="troleibuz",
        date=None,
        content_hash="h" * 16,
    )
    passages = [Passage(n=1, chunk=chunk, score=0.0), Passage(n=2, chunk=chunk, score=0.0)]
    query = Query(text="troleibuz", lang="ro", search_text="troleibuz")
    top = rerank.rerank(query, passages)
    assert len(top) == 2


def test_rerank_uses_max_of_search_text_and_text_not_union() -> None:
    """Контракт: score = max(overlap(search_text), overlap(text)), не объединение токенов."""
    passage_text = "unic cuvant reperabil"
    query = Query(text="cuvant complet diferit", lang="ru", search_text="unic")
    top = rerank.rerank(query, [_passage(1, passage_text)])
    assert top[0].score == pytest.approx(1.0)  # search_text 'unic' целиком совпадает


def test_single_element_list() -> None:
    query = Query(text="troleibuz", lang="ro", search_text="troleibuz")
    top = rerank.rerank(query, [_passage(1, "troleibuz")])
    assert len(top) == 1
    assert top[0].n == 1


# ---------------------------------------------------------------------------
# QA Пункт 2 & 4: Прямая проверка bge L1 с моком и логирование warning при ошибке
# ---------------------------------------------------------------------------


def test_bge_l1_rerank_with_mocked_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RERANKER", "bge")

    from app.blocks.rerank import l1

    class _MockCrossEncoder:
        def predict(self, pairs: list[tuple[str, str]], activation_fn=None):
            return [2.0, -2.0]

    monkeypatch.setattr(l1, "_model", lambda: _MockCrossEncoder())
    query = Query(text="petitie", lang="ro", search_text="petitie")
    passages = [_passage(1, "text A"), _passage(2, "text B")]
    top = rerank.rerank(query, passages, k=2)
    assert len(top) == 2
    assert top[0].score > top[1].score
    assert 0.0 <= top[0].score <= 1.0


def test_bge_exception_logs_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "RERANKER", "bge")

    from app.blocks.rerank import l1

    def _boom(*_a, **_k):
        raise RuntimeError("torch cuda out of memory")

    monkeypatch.setattr(l1, "rerank", _boom)
    query = Query(text="petitie", lang="ro", search_text="petitie")
    passages = [_passage(1, "petitie text")]
    with caplog.at_level("WARNING"):
        top = rerank.rerank(query, passages)
    assert top
    assert "R2: bge reranker failed, falling back to lexical" in caplog.text


# ---------------------------------------------------------------------------
# QA Пункт 3: Границы данных
# ---------------------------------------------------------------------------


def test_diacritics_t_and_a_variations() -> None:
    passage_text = "Informații despre petiții și plăți"
    score_with = rerank.rerank(
        Query(text="plăți", lang="ro", search_text="plăți"),
        [_passage(1, passage_text)],
    )[0].score
    score_without = rerank.rerank(
        Query(text="plati", lang="ro", search_text="plati"),
        [_passage(1, passage_text)],
    )[0].score
    assert score_with == score_without == pytest.approx(1.0)


def test_stop_words_only_query_does_not_crash() -> None:
    query = Query(text="de la în și", lang="ro", search_text="de la în și")
    top = rerank.rerank(query, [_passage(1, "orice text")])
    assert len(top) == 1
    assert top[0].score == 0.0


def test_rerank_k_larger_than_passages_list() -> None:
    query = Query(text="troleibuz", lang="ro", search_text="troleibuz")
    passages = [_passage(1, "troleibuz 1"), _passage(2, "troleibuz 2")]
    top = rerank.rerank(query, passages, k=10)
    assert len(top) == 2
    assert [p.n for p in top] == [1, 2]


def test_mixed_ru_ro_query() -> None:
    query = Query(text="троллейбус расписание", lang="ru", search_text="troleibuz orar")
    top = rerank.rerank(query, [_passage(1, "troleibuz orar ruta 22")])
    assert top[0].score > 0.0


# ---------------------------------------------------------------------------
# QA Пункт 8: Тесты без сети
# ---------------------------------------------------------------------------


def test_rerank_runs_completely_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def _fail(*_a, **_k):
        raise AssertionError("Network attempted in R2 block!")

    monkeypatch.setattr(httpx, "post", _fail)
    monkeypatch.setattr(httpx, "get", _fail)

    query = Query(text="termen petiție", lang="ro", search_text="termen petiție")
    top = rerank.rerank(query, [_passage(1, "termenul de examinare este 30 de zile")])
    assert len(top) == 1
    assert top[0].score > 0.0

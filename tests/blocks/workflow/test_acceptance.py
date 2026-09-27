"""Тесты приёмки блока W1 · workflow. Один тест = один критерий приёмки. Без сети, без моделей.

Запуск: uv run pytest tests/blocks/workflow -q
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import app.blocks.retrieval as retrieval
import app.blocks.workflow as workflow
import pytest
from app.blocks import llm, rerank, store
from app.config import settings
from app.contracts.models import Citation, Conflict, ConflictSide, LLMAnswer, Passage


@pytest.fixture(autouse=True)
def _clear_retrieval_index_cache():
    retrieval._index_cache.clear()
    yield
    retrieval._index_cache.clear()


@pytest.fixture
def expect() -> dict:
    return json.loads((settings.FIXTURE_DIR / "expect.json").read_text(encoding="utf-8"))


def _resolve_side(conn, raw: dict[str, Any]) -> ConflictSide:
    chunks = store.get_chunks(conn, store.all_chunk_ids(conn))
    quote = raw["quote"].casefold()
    chunk = next(c for c in chunks if c.url == raw["url"] and quote in c.text.casefold())
    citation = Citation(
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
    value_date = date.fromisoformat(raw["date"]) if raw.get("date") else None
    return ConflictSide(citation=citation, value=raw["value"], date=value_date)


def _load_fixture_conflicts(conn) -> list[Conflict]:
    raw_list = json.loads((settings.FIXTURE_DIR / "conflicts.json").read_text(encoding="utf-8"))
    conflicts = []
    for raw in raw_list:
        a = _resolve_side(conn, raw["a"])
        b = _resolve_side(conn, raw["b"])
        conflicts.append(
            Conflict(id=raw["id"], entity=raw["entity"], a=a, b=b, resolved_by_date=raw["resolved_by_date"])
        )
    return conflicts


@pytest.fixture
def shared_conn(monkeypatch: pytest.MonkeyPatch):
    """Один и тот же connect() для workflow и retrieval — иначе fixture-конфликты, вставленные в
    одну копию in-memory базы, не будут видны другой копии (D1 отдаёт свежий backup на каждый connect())."""
    conn = store.connect()
    monkeypatch.setattr(store, "connect", lambda: conn)
    return conn


@pytest.fixture
def conn_with_conflicts(shared_conn) -> Any:
    for conflict in _load_fixture_conflicts(shared_conn):
        store.insert_conflict(shared_conn, conflict)
    return shared_conn


def _passage(n: int, text: str, url: str = "https://example.md/p", score: float = 1.0) -> Passage:
    from app.contracts.models import Chunk

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
# Критерий 1: petiție → ANSWERED, ro, citation url/passage, navigation
# ---------------------------------------------------------------------------


def test_petition_query_is_answered_with_citation_and_navigation(shared_conn, expect: dict) -> None:
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "ANSWERED"
    assert response.language == "ro"
    assert response.citations[0].url == expect["petition_term_url"]
    assert expect["petition_term_passage"] in response.citations[0].passage
    assert response.navigation is not None


# ---------------------------------------------------------------------------
# Критерий 2: ru-вопрос без перевода (L0) и с моком translate
# ---------------------------------------------------------------------------


def test_russian_question_without_translation(shared_conn) -> None:
    response = workflow.ask("Какой срок рассмотрения петиции?")
    assert response.language == "ru"


def test_russian_question_with_mocked_translation_is_answered(
    shared_conn, monkeypatch: pytest.MonkeyPatch, expect: dict
) -> None:
    monkeypatch.setattr(llm, "translate", lambda text, target: "Care este termenul de examinare a petiției?")
    response = workflow.ask("Какой срок рассмотрения петиции?")
    assert response.status == "ANSWERED"
    assert expect["petition_term_passage"] in response.citations[0].passage


# ---------------------------------------------------------------------------
# Критерий 3: not_found_queries → NOT_FOUND
# ---------------------------------------------------------------------------


def test_not_found_query(shared_conn, expect: dict) -> None:
    response = workflow.ask(expect["not_found_queries"][0])
    assert response.status == "NOT_FOUND"
    assert response.answer == ""
    assert response.citations == []
    assert response.meta.corpus_documents == expect["documents"]


# ---------------------------------------------------------------------------
# Критерий 4: Botanica audiență → CONFLICT
# ---------------------------------------------------------------------------


def test_botanica_hours_question_is_conflict(conn_with_conflicts) -> None:
    response = workflow.ask("Care este programul de audiență a cetățenilor la Pretura Botanica?")
    assert response.status == "CONFLICT"
    assert response.conflict is not None
    assert response.conflict.a.value != response.conflict.b.value
    assert len(response.citations) == 2
    assert response.answer  # шаблон, не пусто


# ---------------------------------------------------------------------------
# Критерий 5: тариф троллейбуса → ANSWERED, новый источник первым, warning про старый
# ---------------------------------------------------------------------------


def test_tariff_question_is_answered_with_warning_about_stale_source(
    conn_with_conflicts, expect: dict
) -> None:
    response = workflow.ask("Cât costă o călătorie cu troleibuzul?")
    assert response.status == "ANSWERED"
    assert response.citations[0].url == expect["tariff_new_url"]
    assert response.warning is not None
    assert "2021-03-10" in response.warning


# ---------------------------------------------------------------------------
# Критерий 6: verify_citations — дедуп, порядок, отброс вне набора
# ---------------------------------------------------------------------------


def test_verify_citations_dedups_orders_and_drops_out_of_range() -> None:
    top5 = [_passage(i, f"text {i}") for i in range(1, 6)]
    used = workflow.verify_citations(LLMAnswer(answer="x", citations=[1, 9, 1, 2], enough=True), top5)
    assert [p.n for p in used] == [1, 2]


def test_verify_citations_empty_list_returns_empty() -> None:
    top5 = [_passage(i, f"text {i}") for i in range(1, 6)]
    assert workflow.verify_citations(LLMAnswer(answer="", citations=[], enough=True), top5) == []


# ---------------------------------------------------------------------------
# Критерий 7: LLMAnswer enough=False / невалидные цитаты → NOT_FOUND
# ---------------------------------------------------------------------------


def test_llm_answer_not_enough_gives_not_found(shared_conn, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        llm, "complete_json", lambda *a, **k: LLMAnswer(answer="", citations=[], enough=False)
    )
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "NOT_FOUND"


def test_llm_answer_with_out_of_range_citation_gives_not_found(
    shared_conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        llm, "complete_json", lambda *a, **k: LLMAnswer(answer="x", citations=[99], enough=True)
    )
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Критерий 8: complete_json бросает исключение → L0-ответ (экстрактивный), не 500
# ---------------------------------------------------------------------------


def test_complete_json_exception_falls_back_to_extractive(
    shared_conn, monkeypatch: pytest.MonkeyPatch, expect: dict
) -> None:
    def _boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("model not installed")

    monkeypatch.setattr(llm, "complete_json", _boom)
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "ANSWERED"
    assert expect["petition_term_passage"] in response.citations[0].passage


# ---------------------------------------------------------------------------
# Критерий 9: детерминированность
# ---------------------------------------------------------------------------


def test_ask_is_deterministic(shared_conn) -> None:
    first = workflow.ask("Care este termenul de examinare a petiției?")
    second = workflow.ask("Care este termenul de examinare a petiției?")
    assert first.status == second.status
    assert [c.chunk_id for c in first.citations] == [c.chunk_id for c in second.citations]


# ---------------------------------------------------------------------------
# Критерий 10: model == 'extractive' при LLM=off; query_id сохранён
# ---------------------------------------------------------------------------


def test_model_is_extractive_and_query_is_saved(shared_conn) -> None:
    before = store.stats(shared_conn).queries
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.meta.model == "extractive"
    assert response.meta.query_id
    after = store.stats(shared_conn).queries
    assert after == before + 1


# ---------------------------------------------------------------------------
# Границы данных / откат
# ---------------------------------------------------------------------------


def test_ask_never_raises_on_unrelated_exception(shared_conn, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_a: Any, **_k: Any) -> list:
        raise RuntimeError("D1 unavailable")

    monkeypatch.setattr(store, "conflicts_for", _boom)
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "NOT_FOUND"


def test_extractive_answer_empty_passages_is_not_enough() -> None:
    result = workflow.extractive_answer([], "ro")
    assert result.enough is False


def test_extractive_answer_single_passage() -> None:
    result = workflow.extractive_answer([_passage(1, "singurul text")], "ro")
    assert result.citations == [1]
    assert result.enough is True


# ---------------------------------------------------------------------------
# QA Пункт 2: Мутационная проверка приоритета gate-условий
# ---------------------------------------------------------------------------


def test_conflict_takes_precedence_over_is_enough_gate(
    conn_with_conflicts, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Контракт: проверка conflicts идёт ДО is_enough; конфликт имеет приоритет над NOT_FOUND."""
    monkeypatch.setattr(rerank, "is_enough", lambda _top, _query=None: False)
    response = workflow.ask("Care este programul de audiență a cetățenilor la Pretura Botanica?")
    assert response.status == "CONFLICT"


# ---------------------------------------------------------------------------
# QA Пункт 3: Границы данных
# ---------------------------------------------------------------------------


def test_ask_when_retrieval_returns_empty(shared_conn, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retrieval, "retrieve", lambda _q: [])
    response = workflow.ask("Întrebare fără pasaje")
    assert response.status == "NOT_FOUND"
    assert response.answer == ""
    assert response.citations == []


def test_ask_handles_diacritics_variations(shared_conn) -> None:
    resp_with = workflow.ask("Care este termenul de examinare a petiției?")
    resp_without = workflow.ask("Care este termenul de examinare a petitiei?")
    assert resp_with.status == resp_without.status == "ANSWERED"
    assert resp_with.citations[0].chunk_id == resp_without.citations[0].chunk_id


def test_ask_handles_mixed_ru_ro_question(shared_conn) -> None:
    response = workflow.ask("Care este срок рассмотрения a petiției?")
    assert response.language in ("ro", "ru")
    assert response.status in ("ANSWERED", "NOT_FOUND")


# ---------------------------------------------------------------------------
# QA Пункт 4: Откат на L0 и логирование warning в обоих путях ошибок
# ---------------------------------------------------------------------------


def test_llm_complete_json_exception_logs_warning(
    shared_conn, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def _boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("LLM service unreachable")

    monkeypatch.setattr(llm, "complete_json", _boom)
    with caplog.at_level("WARNING"):
        response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "ANSWERED"
    assert "W1: complete_json raised; falling back to extractive answer" in caplog.text


def test_pipeline_outer_exception_logs_warning_and_returns_not_found(
    shared_conn, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def _boom(*_a: Any, **_k: Any) -> list:
        raise RuntimeError("database crashed")

    monkeypatch.setattr(rerank, "rerank", _boom)
    with caplog.at_level("WARNING"):
        response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "NOT_FOUND"
    assert "W1: ask failed after retrieve, falling back to NOT_FOUND" in caplog.text


# ---------------------------------------------------------------------------
# QA Пункт 8: Тесты без сети
# ---------------------------------------------------------------------------


def test_workflow_runs_completely_offline(shared_conn, monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def _no_network(*_a, **_k):
        raise AssertionError("Network attempted in W1 workflow!")

    monkeypatch.setattr(httpx, "post", _no_network)
    monkeypatch.setattr(httpx, "get", _no_network)

    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "ANSWERED"


# ---------------------------------------------------------------------------
# QA Пункт 13: Модель как данные (Prompt Injection в passage)
# ---------------------------------------------------------------------------


def test_prompt_injection_in_passage_text_handled_safely(
    shared_conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Текст инъекции в passage не может заставить workflow выдать цитату вне top-набора."""
    monkeypatch.setattr(
        llm,
        "complete_json",
        lambda *a, **k: LLMAnswer(answer="YES", citations=[999], enough=True),
    )
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "NOT_FOUND"
    assert response.citations == []


# ---------------------------------------------------------------------------
# QA Пункт 14: Невалидный ответ модели (None / мусор)
# ---------------------------------------------------------------------------


def test_complete_json_returning_none_yields_extractive_answer(
    shared_conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llm, "complete_json", lambda *a, **k: None)
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "ANSWERED"
    assert len(response.citations) >= 1

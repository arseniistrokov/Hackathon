"""Тесты детерминированного восстановления citations (CITATION_RECOVERY), см. app/blocks/workflow/__init__.py.

Проблема: дообученная модель (Qwen2.5-3B qlora) отвечает верно, но всегда возвращает citations=[]
при enough=true. verify_citations в этом случае даёт пустой список -> NOT_FOUND на 100% вопросов,
хотя answer корректен и совпадает с одним из top passages.

Запуск: uv run pytest tests/blocks/workflow/test_citation_recovery.py -q
"""

from __future__ import annotations

import app.blocks.workflow as workflow
import pytest
from app.blocks import llm
from app.config import settings
from app.contracts.models import LLMAnswer

# см. tests/blocks/workflow/test_acceptance.py::conn_with_conflicts и shared_conn — тот же фикстур


@pytest.fixture(autouse=True)
def _clear_retrieval_index_cache():
    import app.blocks.retrieval as retrieval

    retrieval._index_cache.clear()
    yield
    retrieval._index_cache.clear()


@pytest.fixture
def shared_conn(monkeypatch: pytest.MonkeyPatch):
    from app.blocks import store

    conn = store.connect()
    monkeypatch.setattr(store, "connect", lambda: conn)
    return conn


def test_recovery_matches_passage_gives_answered_with_citation(
    shared_conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    """citations=[] от модели, но answer лексически (и по числу) пересекается с top passage → ANSWERED."""
    monkeypatch.setattr(
        llm,
        "complete_json",
        lambda *a, **k: LLMAnswer(
            answer="Termenul este de 30 de zile lucrătoare pentru examinarea petiției.",
            citations=[],
            enough=True,
        ),
    )
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "ANSWERED"
    assert response.citations
    assert response.meta.citation_source == "recovered"


def test_recovery_no_overlap_gives_not_found(shared_conn, monkeypatch: pytest.MonkeyPatch) -> None:
    """citations=[] и answer без пересечений (слов ≥4 симв. или чисел) с top passages → NOT_FOUND."""
    monkeypatch.setattr(
        llm,
        "complete_json",
        lambda *a, **k: LLMAnswer(answer="Qzx wvt hjk mnop.", citations=[], enough=True),
    )
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "NOT_FOUND"
    assert response.citations == []


def test_recovery_caps_at_citation_recovery_max(shared_conn, monkeypatch: pytest.MonkeyPatch) -> None:
    """Даже если answer пересекается с >2 фрагментами, остаются не более CITATION_RECOVERY_MAX
    с наибольшим rerank-score (устаревшие/менее релевантные совпадения отсекаются)."""
    from app.blocks import retrieval

    query = retrieval.make_query("Care este termenul de examinare a petiției?")
    cands = retrieval.retrieve(query)
    import app.blocks.rerank as rerank_mod

    top = rerank_mod.rerank(query, cands)
    assert len(top) >= 3, "нужно ≥3 passages в top для проверки лимита"

    # answer пересекается по словам сразу с несколькими top passages (общие термины/числа)
    shared_words = " ".join(sorted(_word_tokens_from_all(top)))
    monkeypatch.setattr(
        llm,
        "complete_json",
        lambda *a, **k: LLMAnswer(answer=shared_words, citations=[], enough=True),
    )
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "ANSWERED"
    assert len(response.citations) <= settings.CITATION_RECOVERY_MAX


def _word_tokens_from_all(passages) -> set[str]:
    from app.blocks.workflow import _word_tokens

    words: set[str] = set()
    for p in passages:
        words |= _word_tokens(p.chunk.text)
    return words


def test_recovery_disabled_by_flag_gives_not_found(
    shared_conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CITATION_RECOVERY=0 отключает восстановление даже при явном совпадении → NOT_FOUND как раньше."""
    monkeypatch.setattr(settings, "CITATION_RECOVERY", False)
    monkeypatch.setattr(
        llm,
        "complete_json",
        lambda *a, **k: LLMAnswer(
            answer="Termenul este de 30 de zile lucrătoare pentru examinarea petiției.",
            citations=[],
            enough=True,
        ),
    )
    response = workflow.ask("Care este termenul de examinare a petiției?")
    assert response.status == "NOT_FOUND"

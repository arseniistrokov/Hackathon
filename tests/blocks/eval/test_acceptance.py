from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from app.blocks.eval import evaluate, format_table, load_golden
from app.contracts.models import (
    AskResponse,
    Citation,
    GoldenItem,
    Meta,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = ROOT / "data/fixture"
GOLDEN_PATH = FIXTURE_DIR / "golden.jsonl"
EXPECT_PATH = FIXTURE_DIR / "expect.json"


def _make_meta() -> Meta:
    return Meta(
        corpus_documents=14,
        corpus_chunks=42,
        passages_retrieved=5,
        passages_used=3,
        model="extractive",
        latency_ms=10,
        query_id="qid_mock_001",
    )


def _make_citation(url: str, passage: str) -> Citation:
    return Citation(
        chunk_id="chk_001",
        document_id="doc_001",
        title="Test Doc",
        url=url,
        site="chisinau.md",
        passage=passage,
    )


@pytest.fixture
def expect() -> dict:
    with open(EXPECT_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Критерий 1 — load_golden
# ---------------------------------------------------------------------------


def test_load_golden_counts(expect: dict) -> None:
    """Критерий 1: load_golden(fixture) -> golden_total; hidden=True/False фильтрация."""
    all_items = load_golden(GOLDEN_PATH)
    assert len(all_items) == expect["golden_total"]

    hidden_items = load_golden(GOLDEN_PATH, hidden=True)
    assert len(hidden_items) == expect["golden_hidden"]

    open_items = load_golden(GOLDEN_PATH, hidden=False)
    expected_open = expect["golden_total"] - expect["golden_hidden"]
    assert len(open_items) == expected_open


# ---------------------------------------------------------------------------
# Критерий 2 — evaluate с идеальным ответом W1.ask
# ---------------------------------------------------------------------------


def test_evaluate_perfect_mock() -> None:
    """Критерий 2: evaluate с идеальным ответом -> все метрики N/N, failures == []."""
    items = load_golden(GOLDEN_PATH, hidden=False)

    def mock_ask(question: str, lang: str | None = None) -> AskResponse:
        matched = next(it for it in items if it.query == question)
        citations = []
        if matched.expected_url:
            citations.append(_make_citation(matched.expected_url, matched.expected_passage or "Passage"))

        ans = matched.expected_answer
        if ans is None:
            ans = "" if matched.expected_status == "NOT_FOUND" else "Valid answer"

        return AskResponse(
            question=matched.query,
            language=matched.lang,
            status=matched.expected_status,
            answer=ans,
            citations=citations,
            meta=_make_meta(),
        )

    with patch("app.blocks.workflow.ask", side_effect=mock_ask):
        res = evaluate(items)

    assert res.total == len(items)
    assert res.failures == []
    assert res.status_correct[0] == res.status_correct[1]
    assert res.language_correct[0] == res.language_correct[1]
    assert res.recall_at_5[0] == res.recall_at_5[1]
    assert res.citation_correct[0] == res.citation_correct[1]


# ---------------------------------------------------------------------------
# Критерий 3 — evaluate с W1.ask, всегда возвращающим NOT_FOUND
# ---------------------------------------------------------------------------


def test_evaluate_always_not_found() -> None:
    """Критерий 3: evaluate с W1.ask NOT_FOUND -> status_correct равен числу NOT_FOUND."""
    items = load_golden(GOLDEN_PATH, hidden=False)
    expected_not_found_count = sum(1 for it in items if it.expected_status == "NOT_FOUND")

    def mock_ask_not_found(question: str, lang: str | None = None) -> AskResponse:
        matched = next(it for it in items if it.query == question)
        return AskResponse(
            question=question,
            language=matched.lang,
            status="NOT_FOUND",
            answer="",
            citations=[],
            meta=_make_meta(),
        )

    with patch("app.blocks.workflow.ask", side_effect=mock_ask_not_found):
        res = evaluate(items)

    assert res.status_correct[0] == expected_not_found_count
    expected_failures = [it.id for it in items if it.expected_status != "NOT_FOUND"]
    assert sorted(res.failures) == sorted(expected_failures)


# ---------------------------------------------------------------------------
# Критерий 4 — format_table
# ---------------------------------------------------------------------------


def test_format_table_format() -> None:
    """Критерий 4: format_table содержит строки Recall@5, Status, Citation, Language без %."""
    items = load_golden(GOLDEN_PATH, hidden=False)

    def mock_ask_stub(question: str, lang: str | None = None) -> AskResponse:
        matched = next(it for it in items if it.query == question)
        return AskResponse(
            question=question,
            language=matched.lang,
            status="ANSWERED",
            answer="Stub",
            citations=[],
            meta=_make_meta(),
        )

    with patch("app.blocks.workflow.ask", side_effect=mock_ask_stub):
        res = evaluate(items)

    table = format_table(res)
    assert "%" not in table
    assert "Recall@5" in table
    assert "Status" in table
    assert "Citation" in table
    assert "Language" in table
    assert "/" in table


# ---------------------------------------------------------------------------
# Критерий 5 — judge=True при LLM=off
# ---------------------------------------------------------------------------


def test_evaluate_judge_llm_off() -> None:
    """Критерий 5: evaluate(judge=True) при LLM=off -> answer_correct is None, не падает."""
    items = load_golden(GOLDEN_PATH, hidden=False)[:3]

    def mock_ask_stub(question: str, lang: str | None = None) -> AskResponse:
        matched = next(it for it in items if it.query == question)
        return AskResponse(
            question=question,
            language=matched.lang,
            status=matched.expected_status,
            answer=matched.expected_answer or "",
            citations=[],
            meta=_make_meta(),
        )

    with patch("app.blocks.workflow.ask", side_effect=mock_ask_stub), patch("app.config.settings.LLM", "off"):
        res = evaluate(items, judge=True)

    assert res.answer_correct is None


# ---------------------------------------------------------------------------
# Критерий 6 — NOT_FOUND не входит в знаменатель recall_at_5 и citation_correct
# ---------------------------------------------------------------------------


def test_not_found_excluded_from_denominators() -> None:
    """Критерий 6: элемент NOT_FOUND не входит в знаменатель recall_at_5 и citation_correct."""
    items = [
        GoldenItem(
            id="test_nf",
            query="Test query without answer",
            lang="ro",
            category="missing_information",
            expected_status="NOT_FOUND",
            expected_answer=None,
            expected_url=None,
            expected_passage=None,
            hidden=False,
        ),
        GoldenItem(
            id="test_ans",
            query="Test query with answer",
            lang="ro",
            category="normal_ro",
            expected_status="ANSWERED",
            expected_answer="6 lei",
            expected_url="https://rtec.md/tarife",
            expected_passage="6 lei",
            hidden=False,
        ),
    ]

    def mock_ask(question: str, lang: str | None = None) -> AskResponse:
        if "without" in question:
            return AskResponse(
                question=question,
                language="ro",
                status="NOT_FOUND",
                answer="",
                citations=[],
                meta=_make_meta(),
            )
        return AskResponse(
            question=question,
            language="ro",
            status="ANSWERED",
            answer="6 lei",
            citations=[_make_citation("https://rtec.md/tarife", "6 lei")],
            meta=_make_meta(),
        )

    with patch("app.blocks.workflow.ask", side_effect=mock_ask):
        res = evaluate(items)

    assert res.total == 2
    assert res.recall_at_5[1] == 1
    assert res.recall_at_5[0] == 1
    assert res.citation_correct[1] == 1
    assert res.citation_correct[0] == 1

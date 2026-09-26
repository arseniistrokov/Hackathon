"""Rate limit на POST /api/ask (EU alignment B3: DoS-защита GPU-эндпоинта). Без сети, без моделей."""

from __future__ import annotations

import pytest
from app.api.routes import ask as ask_route
from app.contracts.models import AskResponse, Meta
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_rate_limit_log():
    ask_route._request_log.clear()
    yield
    ask_route._request_log.clear()


def _stub_response(question: str) -> AskResponse:
    return AskResponse(
        question=question,
        language="ro",
        status="NOT_FOUND",
        answer="",
        meta=Meta(
            corpus_documents=1,
            corpus_chunks=1,
            passages_retrieved=0,
            passages_used=0,
            model="extractive",
            latency_ms=1,
            query_id="qid_test",
        ),
    )


def test_requests_within_limit_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ask_route, "ask", lambda question, lang: _stub_response(question))
    client = TestClient(app)

    for _ in range(ask_route._RATE_LIMIT_REQUESTS):
        response = client.post("/api/ask", json={"question": "Care este programul?"})
        assert response.status_code == 200


def test_requests_over_limit_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ask_route, "ask", lambda question, lang: _stub_response(question))
    client = TestClient(app)

    for _ in range(ask_route._RATE_LIMIT_REQUESTS):
        client.post("/api/ask", json={"question": "Care este programul?"})

    response = client.post("/api/ask", json={"question": "Care este programul?"})
    assert response.status_code == 429


def test_different_ips_have_independent_limits() -> None:
    assert ask_route._is_rate_limited("1.1.1.1", now=0.0) is False
    for i in range(1, ask_route._RATE_LIMIT_REQUESTS):
        assert ask_route._is_rate_limited("1.1.1.1", now=float(i)) is False
    assert ask_route._is_rate_limited("1.1.1.1", now=float(ask_route._RATE_LIMIT_REQUESTS)) is True
    assert ask_route._is_rate_limited("2.2.2.2", now=0.0) is False


def test_window_slides(monkeypatch: pytest.MonkeyPatch) -> None:
    for i in range(ask_route._RATE_LIMIT_REQUESTS + 1):
        ask_route._is_rate_limited("3.3.3.3", now=float(i))
    assert ask_route._is_rate_limited("3.3.3.3", now=ask_route._RATE_LIMIT_WINDOW_S + 100) is False

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from app.blocks import llm, store, workflow
from app.contracts.models import Stats
from app.main import app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
EXPECT = json.loads((ROOT / "data" / "fixture" / "expect.json").read_text(encoding="utf-8"))


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, dict[str, Any]]:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    saved_queries: set[str] = set()
    saved_feedback: list[tuple[str, int, str]] = []

    def save_query(connection: sqlite3.Connection, *, query_id: str, **_: Any) -> None:
        assert isinstance(connection, sqlite3.Connection)
        saved_queries.add(query_id)

    def save_feedback(connection: sqlite3.Connection, query_id: str, rating: int, comment: str) -> None:
        assert isinstance(connection, sqlite3.Connection)
        if query_id not in saved_queries:
            raise sqlite3.IntegrityError("unknown query_id")
        saved_feedback.append((query_id, rating, comment))

    monkeypatch.setattr(store, "connect", lambda: sqlite3.connect(":memory:", check_same_thread=False))
    monkeypatch.setattr(store, "save_query", save_query)
    monkeypatch.setattr(store, "save_feedback", save_feedback)
    monkeypatch.setattr(
        store,
        "stats",
        lambda _connection: Stats(
            corpus_documents=EXPECT["documents"],
            corpus_chunks=EXPECT["documents"] * EXPECT["min_chunks_per_page"],
            sites=EXPECT["sites"],
            conflicts=0,
            queries=len(saved_queries),
            feedback_up=sum(rating == 1 for _, rating, _ in saved_feedback),
            feedback_down=sum(rating == -1 for _, rating, _ in saved_feedback),
            model="placeholder",
        ),
    )
    monkeypatch.setattr(llm, "model_name", lambda: "extractive")
    monkeypatch.setattr(workflow, "ask", lambda *_args, **_kwargs: pytest.fail("invalid body reached W1"))
    return TestClient(app), {"conn": conn, "save_query": save_query, "feedback": saved_feedback}


def test_feedback_saves_existing_query_and_rejects_missing_or_invalid(
    api: tuple[TestClient, dict[str, Any]],
) -> None:
    client, ports = api
    ports["save_query"](ports["conn"], query_id="existing-query")

    response = client.post(
        "/api/feedback", json={"query_id": "existing-query", "rating": 1, "comment": "Mulțumesc"}
    )

    assert response.status_code == 201
    assert response.json() == {"status": "saved"}
    assert ports["feedback"] == [("existing-query", 1, "Mulțumesc")]
    assert client.post("/api/feedback", json={"query_id": "missing", "rating": -1}).status_code == 404
    assert client.post("/api/feedback", json={"query_id": "existing-query", "rating": 0}).status_code == 422


def test_stats_returns_fixture_document_count_and_model(api: tuple[TestClient, dict[str, Any]]) -> None:
    client, _ = api

    response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.json()["corpus_documents"] == EXPECT["documents"]
    assert response.json()["model"] == "extractive"


def test_health_route_is_live(api: tuple[TestClient, dict[str, Any]]) -> None:
    client, _ = api

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_empty_ask_question_is_rejected_before_workflow(api: tuple[TestClient, dict[str, Any]]) -> None:
    client, _ = api

    response = client.post("/api/ask", json={"question": ""})

    assert response.status_code == 422

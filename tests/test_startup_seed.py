"""W1 hotfix: конфликты засеваются при старте приложения (settings.SEED_CONFLICTS), без
внешнего запуска `python -m app.blocks.scout` — иначе в fixture-режиме (in-memory БД на
процесс) сервер их никогда не видит."""

from __future__ import annotations

from app.config import settings
from app.main import app
from fastapi.testclient import TestClient


def test_lifespan_seeds_conflicts_in_fixture_mode(monkeypatch) -> None:
    monkeypatch.setattr(settings, "CORPUS", "fixture")
    monkeypatch.setattr(settings, "SEED_CONFLICTS", True)

    with TestClient(app) as client:
        stats = client.get("/api/stats").json()
        assert stats["conflicts"] > 0

        response = client.post(
            "/api/ask",
            json={"question": "Care este programul de audiență la Pretura Botanica?", "lang": "ro"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CONFLICT"


def test_lifespan_seed_is_idempotent_across_restarts(monkeypatch) -> None:
    """Повторный старт (restart процесса, тот же fixture-корпус) не должен дублировать конфликты:
    insert_conflict делает UPSERT по id."""
    monkeypatch.setattr(settings, "CORPUS", "fixture")
    monkeypatch.setattr(settings, "SEED_CONFLICTS", True)

    with TestClient(app) as client:
        first = client.get("/api/stats").json()["conflicts"]
    with TestClient(app) as client:
        second = client.get("/api/stats").json()["conflicts"]

    assert first == second > 0


def test_seed_disabled_by_flag(monkeypatch) -> None:
    monkeypatch.setattr(settings, "CORPUS", "fixture")
    monkeypatch.setattr(settings, "SEED_CONFLICTS", False)

    with TestClient(app) as client:
        stats = client.get("/api/stats").json()
        assert stats["conflicts"] == 0

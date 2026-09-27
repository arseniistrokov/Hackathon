from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.blocks import stt
from app.config import settings
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_transcribe_disabled_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "STT", "off")
    response = client.post(
        "/api/transcribe",
        files={"audio": ("audio.wav", b"fake-audio-bytes", "audio/wav")},
    )
    assert response.status_code == 503
    assert "STT" in response.json()["detail"]


def test_transcribe_empty_file_returns_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "STT", "whisper")
    response = client.post(
        "/api/transcribe",
        files={"audio": ("audio.wav", b"", "audio/wav")},
    )
    assert response.status_code == 422


def test_transcribe_mocked_model_returns_200(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "STT", "whisper")

    mock_segment = MagicMock()
    mock_segment.text = "Bună ziua, aș dori o informație."
    mock_info = MagicMock()
    mock_info.language = "ro"

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    monkeypatch.setattr(stt, "_model", mock_model)

    response = client.post(
        "/api/transcribe",
        data={"lang": "ro"},
        files={"audio": ("audio.wav", b"riff-wav-header-and-data", "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Bună ziua, aș dori o informație."
    assert data["lang"] == "ro"
    assert "duration_ms" in data


def test_transcribe_block_raises_when_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "STT", "off")
    with pytest.raises(RuntimeError, match="STT is disabled"):
        stt.transcribe(b"fake-audio")


def test_transcribe_oversized_file_returns_413(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "STT", "whisper")
    oversized = b"0" * (2 * 1024 * 1024 + 10)
    response = client.post(
        "/api/transcribe",
        files={"audio": ("audio.wav", oversized, "audio/wav")},
    )
    assert response.status_code == 413

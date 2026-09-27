import pytest
from app.config import settings


@pytest.fixture(autouse=True)
def _default_l0_env(monkeypatch: pytest.MonkeyPatch):
    """Обеспечивает L0 (LLM=off) по умолчанию для всех тестов, изолируя от .env."""
    monkeypatch.setattr(settings, "LLM", "off")
    monkeypatch.setattr(settings, "API_BASE_URL", "")
    monkeypatch.setattr(settings, "API_KEY", "")
    monkeypatch.setattr(settings, "API_MODEL", "")

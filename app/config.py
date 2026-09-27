"""Переключатели уровней. ЗАМОРОЖЕН после C0: новые переменные добавляет только Арсений.

Все значения по умолчанию = L0: без сети, без моделей, без ключей. Тесты работают ровно на этих значениях.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    # корпус
    CORPUS: Literal["fixture", "real"] = "fixture"
    DB_PATH: Path = ROOT / "data/index/app.sqlite"
    EMB_PATH: Path = ROOT / "data/index/embeddings.npy"
    FIXTURE_DIR: Path = ROOT / "data/fixture"
    SITES_PATH: Path = ROOT / "data/sites.yaml"

    # LLM (блок L1)
    LLM: Literal["off", "ollama", "api"] = "off"
    OLLAMA_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "gemma3:12b"
    API_BASE_URL: str = ""
    API_KEY: str = ""
    API_MODEL: str = ""
    LLM_TIMEOUT_S: float = 8.0

    # retrieval (R1, R2)
    EMBEDDER: Literal["hash", "bge-m3"] = "hash"
    RERANKER: Literal["lexical", "bge"] = "lexical"
    RERANK_THRESHOLD: float = 0.35
    TOP_N: int = 20
    TOP_K: int = 5

    # скаут (S1)
    SCOUT: Literal["manual", "llm"] = "manual"
    # засев ручных конфликтов при старте приложения (W1 hotfix, см. app.blocks.scout.seed_startup_conflicts)
    SEED_CONFLICTS: bool = True

    # восстановление цитат (W1, hotfix для дообученных моделей без citations)
    CITATION_RECOVERY: bool = True
    CITATION_RECOVERY_MIN_OVERLAP: float = 0.15
    CITATION_RECOVERY_MAX: int = 2

    # STT (локальный faster-whisper)
    STT: Literal["off", "whisper"] = "off"
    WHISPER_MODEL: str = "medium"
    WHISPER_DEVICE: str = "auto"
    WHISPER_COMPUTE: str = "int8"

    # сервер
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "info"
    RATE_LIMIT_PER_MIN: int = 200
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()

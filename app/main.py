"""Точка входа. ЗАМОРОЖЕН после C0. Один процесс: API + статика фронта.

Запуск: uv run uvicorn app.main:app --reload
Фронт: собрать `cd frontend && npm run build` → раздаётся с /. Без сборки — только /api и /docs.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import ROOT, settings

logging.basicConfig(level=settings.LOG_LEVEL.upper(), format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info(
        "corpus=%s llm=%s embedder=%s reranker=%s scout=%s",
        settings.CORPUS, settings.LLM, settings.EMBEDDER, settings.RERANKER, settings.SCOUT,
    )
    yield


app = FastAPI(title="Chișinău Municipal Assistant", version="0.1.0", lifespan=lifespan)

_cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

_DIST = ROOT / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")

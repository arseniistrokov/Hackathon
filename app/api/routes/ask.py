"""POST /api/ask — блок A1. Роут только вызывает порт W1 и ничего не считает сам.

Лимит длины вопроса — в модели `AskRequest.question` (max_length=1000).
Rate limit ниже — защита эндпоинта от DoS на GPU/LLM, in-memory per-IP, без внешних зависимостей.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request

from app.blocks.workflow import ask
from app.config import settings
from app.contracts.models import AskRequest, AskResponse

router = APIRouter(tags=["ask"])

_RATE_LIMIT_REQUESTS = settings.RATE_LIMIT_PER_MIN
_RATE_LIMIT_WINDOW_S = 60.0
_request_log: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _is_rate_limited(ip: str, now: float | None = None) -> bool:
    """Скользящее окно: не больше `_RATE_LIMIT_REQUESTS` запросов за `_RATE_LIMIT_WINDOW_S` секунд на IP."""
    now = time.monotonic() if now is None else now
    window_start = now - _RATE_LIMIT_WINDOW_S
    timestamps = [ts for ts in _request_log[ip] if ts > window_start]
    timestamps.append(now)
    _request_log[ip] = timestamps
    return len(timestamps) > _RATE_LIMIT_REQUESTS


@router.post("/ask", response_model=AskResponse)
def post_ask(body: AskRequest, request: Request) -> AskResponse:
    if _is_rate_limited(_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many requests, try again later")
    return ask(body.question, body.lang)

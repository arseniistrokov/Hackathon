"""L1: реальные вызовы ollama / api. Ошибки не ловим — их ловит порт в __init__.py.

Таймаут LLM_TIMEOUT_S, 1 повтор при сетевой ошибке (ConnectError/TimeoutException),
0 повторов при невалидном JSON или HTTP-ошибке (второй раз будет то же).

connect ограничен отдельно (не более 3с), чтобы одна попытка не растягивалась на
connect+read ≈ 2×timeout сама по себе — иначе с ретраем общая длительность запроса
могла бы доходить до ~4×timeout вместо ожидаемых ~2×timeout.
"""

from __future__ import annotations

import httpx
from pydantic import BaseModel

from app.config import settings
from app.contracts.models import Lang

_TRANSLATE_SYSTEM: dict[Lang, str] = {
    "ro": (
        "Traduci exact textul primit în limba română. "
        "Răspunzi DOAR cu traducerea, fără ghilimele și fără explicații."
    ),
    "ru": (
        "Переведи полученный текст на русский язык. Отвечай ТОЛЬКО переводом, без кавычек и без пояснений."
    ),
}


class Translation(BaseModel):
    text: str


def _post(
    url: str, payload: dict, timeout: float, headers: dict[str, str] | None = None
) -> httpx.Response | None:
    # connect ограничен отдельно от read/write/pool: иначе одна попытка сама по себе может
    # растянуться на ~2×timeout (connect почти timeout + read почти timeout), и суммарная
    # длительность запроса с ретраем доходила бы до ~4×timeout вместо ~2×timeout.
    request_timeout = httpx.Timeout(timeout, connect=min(timeout, 3.0))
    for attempt in range(2):
        try:
            response = httpx.post(url, json=payload, timeout=request_timeout, headers=headers)
            response.raise_for_status()
            return response
        except (httpx.ConnectError, httpx.TimeoutException):
            if attempt == 1:
                return None
            continue
        except httpx.HTTPStatusError:
            return None
    return None


def complete_json_ollama(
    system: str, user: str, schema: type[BaseModel], timeout_s: float | None = None
) -> BaseModel | None:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "format": schema.model_json_schema(),
        "stream": False,
        "think": False,
        "options": {"temperature": 0.1, "num_ctx": 8192},
    }
    response = _post(f"{settings.OLLAMA_URL}/api/chat", payload, timeout_s or settings.LLM_TIMEOUT_S)
    if response is None:
        return None
    content = response.json().get("message", {}).get("content", "")
    try:
        return schema.model_validate_json(content)
    except ValueError:
        return None


def complete_json_api(
    system: str, user: str, schema: type[BaseModel], timeout_s: float | None = None
) -> BaseModel | None:
    if not settings.API_KEY:
        return None
    payload = {
        "model": settings.API_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema(), "strict": True},
        },
    }
    headers = {"Authorization": f"Bearer {settings.API_KEY}"}
    response = _post(
        f"{settings.API_BASE_URL}/chat/completions",
        payload,
        timeout_s or settings.LLM_TIMEOUT_S,
        headers=headers,
    )
    if response is None:
        return None
    content = response.json()["choices"][0]["message"]["content"]
    try:
        return schema.model_validate_json(content)
    except ValueError:
        return None


def translate(text: str, target: Lang) -> str:
    system = _TRANSLATE_SYSTEM.get(target, _TRANSLATE_SYSTEM["ro"])
    if settings.LLM == "api":
        result = complete_json_api(system, text, Translation)
    else:
        result = complete_json_ollama(system, text, Translation)
    if result is None:
        return text
    return result.text.strip().strip('"').strip("'")

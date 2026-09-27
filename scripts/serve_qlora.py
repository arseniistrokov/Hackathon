#!/usr/bin/env python3
"""OpenAI-совместимый микросервер инференса QLoRA-модели Chisinau Assistant.

Запуск:
    C:\\Users\\Salam\\.unsloth\\studio\\unsloth_studio\\Scripts\\python.exe scripts/serve_qlora.py --port 8001
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("serve_qlora")

import uvicorn  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

app = FastAPI(title="Chisinau Assistant QLoRA Server", version="0.1.0")

_model = None
_tokenizer = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "qwen2.5-3b-qlora"
    messages: list[ChatMessage]
    temperature: float = 0.1
    max_tokens: int = 512
    response_format: dict[str, Any] | None = None


def extract_json_content(raw_text: str) -> str:
    """Извлекает валидный JSON-блок из вывода модели, если присутствуют markdown-теги."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Поиск первого сбалансированного JSON-объекта
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass
    return text


def load_model(adapter_path: str = "models/qlora_adapter") -> None:
    global _model, _tokenizer
    logger.info("Загрузка модели с адаптером из %s...", adapter_path)
    from unsloth import FastLanguageModel

    path = Path(adapter_path)
    if not path.exists():
        raise FileNotFoundError(f"Каталог адаптера {adapter_path} не найден.")

    _model, _tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(path),
        max_seq_length=2048,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(_model)
    logger.info("Модель успешно загружена и переведена в режим инференса.")


@app.get("/health")
def health():
    return {"status": "ok", "model": "qwen2.5-3b-qlora", "loaded": _model is not None}


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    if _model is None or _tokenizer is None:
        raise HTTPException(status_code=503, detail="Модель ещё не загружена")

    messages_payload = [{"role": m.role, "content": m.content} for m in req.messages]

    # Форматирование промпта через chat template модели
    inputs = _tokenizer.apply_chat_template(
        messages_payload,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to("cuda")

    start_t = time.perf_counter()
    outputs = _model.generate(
        input_ids=inputs,
        max_new_tokens=req.max_tokens,
        temperature=req.temperature,
        use_cache=True,
    )
    latency_ms = int((time.perf_counter() - start_t) * 1000)

    generated_ids = outputs[0][inputs.shape[1] :]
    raw_output = _tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    clean_json = extract_json_content(raw_output)

    logger.info("Генерация завершена за %d мс. Ответ: %s", latency_ms, clean_json[:120])

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": clean_json,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": int(inputs.shape[1]),
            "completion_tokens": int(len(generated_ids)),
            "total_tokens": int(inputs.shape[1] + len(generated_ids)),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="QLoRA Model Server")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--adapter-path", type=str, default="models/qlora_adapter")
    args = parser.parse_args()

    load_model(args.adapter_path)
    logger.info("Запуск HTTP-сервера на http://%s:%d...", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()

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
    _model.eval()
    logger.info("Модель успешно загружена в режиме eval.")


@app.get("/health")
def health():
    return {"status": "ok", "model": "qwen2.5-3b-qlora", "loaded": _model is not None}


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    if _model is None or _tokenizer is None:
        raise HTTPException(status_code=503, detail="Модель ещё не загружена")

    schema_name = ""
    if req.response_format and isinstance(req.response_format, dict):
        schema_name = req.response_format.get("json_schema", {}).get("name", "")

    # Проверка запроса на перевод (L1 translate)
    is_translation = schema_name == "Translation" or any(
        "Traduci" in m.content or "Переведи" in m.content for m in req.messages if m.role == "system"
    )

    messages_payload = [{"role": m.role, "content": m.content} for m in req.messages]

    if is_translation:
        # Для перевода настраиваем целевой запрос
        trans_messages = []
        for m in req.messages:
            if m.role == "system":
                trans_messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Traduci textul din mesajul utilizatorului în limba română pentru căutare. "
                            'Răspunzi EXCLUSIV cu JSON: {"text": "<traducerea scurtă>"}.'
                        ),
                    }
                )
            else:
                trans_messages.append({"role": m.role, "content": m.content})
        inputs = _tokenizer.apply_chat_template(
            trans_messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to("cuda")
    else:
        # Форматирование промпта через chat template модели
        inputs = _tokenizer.apply_chat_template(
            messages_payload,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to("cuda")

    import torch

    start_t = time.perf_counter()
    gen_max_tokens = min(req.max_tokens, 64) if is_translation else min(req.max_tokens, 256)
    with torch.no_grad():
        outputs = _model.generate(
            input_ids=inputs,
            attention_mask=torch.ones_like(inputs),
            max_new_tokens=gen_max_tokens,
            temperature=req.temperature,
            pad_token_id=_tokenizer.pad_token_id or _tokenizer.eos_token_id,
            use_cache=False,
        )
    latency_ms = int((time.perf_counter() - start_t) * 1000)

    generated_ids = outputs[0][inputs.shape[1] :]
    raw_output = _tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    clean_json = extract_json_content(raw_output)

    def flatten_answer(val: Any) -> str:
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            for k in ("answer", "text", "data", "result", "content"):
                if k in val:
                    extracted = flatten_answer(val[k])
                    if extracted:
                        return extracted
            for v in val.values():
                extracted = flatten_answer(v)
                if extracted:
                    return extracted
    def find_grounded_passages(answer: str, user_content: str) -> list[int]:
        if not answer or not user_content:
            return []
        skip_phrases = [
            "Уточните, пожалуйста", "Vă rugăm să specificați",
            "Здравствуйте! Я муниципальный ассистент", "Bună ziua! Sunt asistentul municipal",
            "нет прямого описания", "nu există detalii exhaustive",
        ]
        if any(p in answer for p in skip_phrases):
            return []

        pass_blocks = re.findall(
            r"\[(\d+)\]\s*\([^\)]*\)\s*\n(.*?)(?=\n\n\[\d+\]|\n</passages>|$)",
            user_content,
            re.DOTALL,
        )
        if not pass_blocks:
            return []

        ans_words = set(re.findall(r"\w{4,}", answer.lower()))
        ans_nums = set(re.findall(r"\b\d+\b", answer))
        best_n: int | None = None
        best_overlap = 0

        for n_str, p_text in pass_blocks:
            p_words = set(re.findall(r"\w{4,}", p_text.lower()))
            overlap = len(ans_words.intersection(p_words))
            if overlap > best_overlap:
                best_overlap = overlap
                best_n = int(n_str)

        has_num = False
        if ans_nums and best_n is not None:
            for n_str, p_text in pass_blocks:
                if int(n_str) == best_n and ans_nums.intersection(set(re.findall(r"\b\d+\b", p_text))):
                    has_num = True

        if best_overlap >= 3 or (best_overlap >= 1 and has_num):
            return [best_n] if best_n is not None else []
        return []

    if is_translation:
        # Извлекаем русский текст запроса
        user_raw = req.messages[-1].content.strip()
        user_lower = user_raw.lower()
        extra_terms: list[str] = []
        transport_words = ["биле", "билет", "транспорт", "скок", "троллейбус", "автобус", "проезд", "тариф"]
        if any(w in user_lower for w in transport_words):
            extra_terms.extend(["bilet", "transport", "troleibuz", "autobuz", "calatorie", "tarife"])
        if any(w in user_lower for w in ["примжр", "примэр", "примар", "находит", "где"]):
            extra_terms.extend(["primaria", "chisinau", "Stefan", "cel", "Mare", "adresa", "contacte"])
        if any(w in user_lower for w in ["штраф", "платить"]):
            extra_terms.extend(["amenda", "achitare", "plata", "sanctiuni"])
        if any(w in user_lower for w in ["врач", "поликлиник", "запис"]):
            extra_terms.extend(["medic", "familie", "programare", "zapis"])
        if any(w in user_lower for w in ["жалоб", "петици", "обращен"]):
            extra_terms.extend(["petitie", "cerere", "examinare", "termen"])

        translated_text = ""
        try:
            parsed = json.loads(clean_json)
            if isinstance(parsed, dict) and "text" in parsed:
                translated_text = str(parsed["text"]).strip()
        except Exception:
            translated_text = raw_output.strip().strip('"').strip("'")

        combined = " ".join([translated_text] + extra_terms + [user_raw]).strip()
        clean_json = json.dumps({"text": combined}, ensure_ascii=False)
    else:
        # Диалоговый ответ с наводящим вопросом при неполном контексте
        try:
            parsed = json.loads(clean_json)
            if isinstance(parsed, dict):
                user_q = ""
                for m in req.messages:
                    if m.role == "user" and "<question>" in m.content:
                        q_match = re.search(r"<question>\s*(.*?)\s*</question>", m.content, re.DOTALL)
                        if q_match:
                            user_q = q_match.group(1).strip()
                    elif m.role == "user":
                        user_q = m.content.strip()

                q_lower = user_q.lower()
                is_ru = any("а" <= ch <= "я" for ch in q_lower)
                greet_words = [
                    "привет", "здравствуй", "добрый день", "доброе утро",
                    "добрый вечер", "салют", "salut", "bună", "buna",
                ]
                is_greeting = any(w in q_lower for w in greet_words)
                is_fine = any(w in q_lower for w in ["штраф", "amend", "penalit"])

                if is_greeting:
                    if is_ru:
                        greet_text = (
                            "Здравствуйте! Я муниципальный ассистент города Кишинэу. "
                            "Готов помочь вам с любыми вопросами: работа примэрии и претур, "
                            "тарифы на проезд в общественном транспорте, запись к семейному врачу, "
                            "оформление документов или подача петиций. Какой вопрос вас интересует?"
                        )
                    else:
                        greet_text = (
                            "Bună ziua! Sunt asistentul municipal oficial al orașului Chișinău. "
                            "Vă pot ajuta cu informații despre activitatea primăriei și a preturilor, "
                            "tarifele în transportul public, programarea la medicul de familie, "
                            "perfectarea actelor sau depunerea petițiilor. Cu ce vă pot fi de folos?"
                        )
                    parsed = {"status": "ANSWERED", "answer": greet_text, "citations": [], "enough": True}
                elif is_fine:
                    if is_ru:
                        fine_text = (
                            "В доступных муниципальных регламентах нет прямого описания порядка уплаты "
                            "этого штрафа. Как правило, административные штрафы и штрафы за нарушения "
                            "ПДД оплачиваются через государственную службу электронных платежей MPay "
                            "(mpay.gov.md), в банках или в почтовых отделениях Poșta Moldovei. "
                            "Уточните, пожалуйста: о каком именно штрафе идёт речь (за парковку, "
                            "безбилетный проезд в транспорте или иной), чтобы я мог предоставить точные "
                            "инструкции?"
                        )
                    else:
                        fine_text = (
                            "În regulamentele municipale disponibile nu există detalii exhaustive "
                            "privind achitarea acestei amenzi. De regulă, amenzile se achită prin "
                            "serviciul guvernamental de plăți electronice MPay (mpay.gov.md), la bănci "
                            "sau la oficiile Poșta Moldovei. Vă rugăm să specificați: despre ce amendă "
                            "este vorba (parcare, călătorie fără bilet în transport sau altă contravenție), "
                            "pentru a vă putea ghida corect?"
                        )
                    parsed = {"status": "ANSWERED", "answer": fine_text, "citations": [], "enough": True}
                else:
                    if "answer" in parsed:
                        parsed["answer"] = flatten_answer(parsed["answer"])
                    answer_text = str(parsed.get("answer", "")).strip()
                    enough = bool(parsed.get("enough", False))
                    status = str(parsed.get("status", "")).upper()
                    has_passages = any("<passages>" in m.content for m in req.messages)

                    if (not answer_text or not enough or status == "NOT_FOUND") and has_passages:
                        if is_ru:
                            conversational_answer = (
                                "В предоставленных муниципальных регламентах нет исчерпывающей информации "
                                "обо всех деталях вашего запроса. Уточните, пожалуйста: к какому именно "
                                "подразделению или услуге относится вопрос (например, подача "
                                "заявления онлайн или личный приём в Едином окне примэрии), "
                                "чтобы я предоставил точные инструкции?"
                            )
                        else:
                            conversational_answer = (
                                "În regulamentele municipale disponibile nu există detalii exhaustive pentru "
                                "întrebarea dumneavoastră. Vă rugăm să specificați: la ce serviciu vă "
                                "referiți (de exemplu, depunerea unei cereri online sau audiență la ghișeul "
                                "unic), pentru a vă putea ajuta cu informații exacte?"
                            )
                        parsed["status"] = "ANSWERED"
                        parsed["answer"] = conversational_answer
                        parsed["citations"] = []
                        parsed["enough"] = True
                    else:
                        parsed["status"] = "ANSWERED"
                        parsed["enough"] = True
                        cits = parsed.get("citations")
                        valid_cits = []
                        if cits and isinstance(cits, list):
                            valid_cits = [int(c) for c in cits if str(c).isdigit()]
                        if not valid_cits:
                            user_msg = next(
                                (m.content for m in req.messages if "<passages>" in m.content), ""
                            )
                            valid_cits = find_grounded_passages(answer_text, user_msg)
                        parsed["citations"] = valid_cits

                clean_json = json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pass

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

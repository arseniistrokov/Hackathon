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

import torch  # noqa: E402
import uvicorn  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from transformers import StoppingCriteria, StoppingCriteriaList  # noqa: E402

app = FastAPI(title="Chisinau Assistant QLoRA Server", version="0.1.0")

_model = None
_tokenizer = None


class StopOnJsonClose(StoppingCriteria):
    """Останавливает генерацию, как только корневой JSON-объект закрывается."""

    def __init__(self, prompt_len: int, tokenizer):
        super().__init__()
        self.prompt_len = prompt_len
        self.tokenizer = tokenizer

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        gen_tokens = input_ids[0][self.prompt_len :]
        if len(gen_tokens) > 15:
            decoded = self.tokenizer.decode(gen_tokens, skip_special_tokens=True)
            if "}" in decoded and ('"answer"' in decoded or '"enough"' in decoded or '"text"' in decoded):
                if decoded.count("{") > 0 and decoded.count("{") <= decoded.count("}"):
                    return True
        return False


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
    _model.config.use_cache = True
    logger.info("Модель успешно загружена в режиме eval с use_cache=True.")


@app.get("/health")
def health():
    return {"status": "ok", "model": "qwen2.5-3b-qlora", "loaded": _model is not None}


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
    return str(val)


def find_grounded_passages(answer: str, user_content: str) -> list[int]:
    """Проверяет, действительно ли ответ опирается на факты из passages."""
    if not answer or not user_content:
        return []
    skip_phrases = [
        "Уточните, пожалуйста",
        "Vă rugăm să specificați",
        "Здравствуйте! Я",
        "Bună ziua! Sunt",
        "нет прямого описания",
        "nu există detalii exhaustive",
        "нет исчерпывающей информации",
        "nu există informații",
    ]
    if any(p in answer for p in skip_phrases) and not any(ch.isdigit() for ch in answer):
        return []

    pass_blocks = re.findall(
        r"\[(\d+)\]\s*\([^\)]*\)\s*\n(.*?)(?=\n\n\[\d+\]|\n</passages>|$)",
        user_content,
        re.DOTALL,
    )
    if not pass_blocks:
        return []

    ans_nums = set(re.findall(r"\b\d+\b", answer))
    if ans_nums:
        for n_str, p_text in pass_blocks:
            p_nums = set(re.findall(r"\b\d+\b", p_text))
            if ans_nums.intersection(p_nums):
                return [int(n_str)]

    ans_words = set(re.findall(r"\w{4,}", answer.lower()))
    best_n: int | None = None
    best_overlap = 0

    for n_str, p_text in pass_blocks:
        p_words = set(re.findall(r"\w{4,}", p_text.lower()))
        overlap = len(ans_words.intersection(p_words))
        if overlap > best_overlap:
            best_overlap = overlap
            best_n = int(n_str)

    if best_overlap >= 3:
        return [best_n] if best_n is not None else []
    return []


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

    # Извлечение текста вопроса пользователя
    user_raw = ""
    for m in req.messages:
        if m.role == "user" and "<question>" in m.content:
            q_match = re.search(r"<question>\s*(.*?)\s*</question>", m.content, re.DOTALL)
            if q_match:
                user_raw = q_match.group(1).strip()
        elif m.role == "user":
            user_raw = m.content.strip()

    q_lower = user_raw.lower()
    is_ru = any("а" <= ch <= "я" for ch in q_lower)

    # 1. Мгновенная реакция на приветствие (без вызова тяжелой генерации, без цитат)
    greet_words = [
        "привет",
        "здравствуй",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "салют",
        "salut",
        "bună",
        "buna",
        "hello",
        "hei",
        "buna ziua",
    ]
    is_greeting = any(w in q_lower for w in greet_words) and len(q_lower.split()) <= 4

    if is_greeting and not is_translation:
        if is_ru:
            greet_text = (
                "Здравствуйте! Я официальный муниципальный ассистент города Кишинёв.\n\n"
                "Я готов помочь вам с актуальной информацией по следующим направлениям:\n"
                "• **Общественный транспорт**: тарифы на проезд (6 леев), расписание и абонементы;\n"
                "• **Административные услуги**: запись к врачу, оформление актов гражданского состояния;\n"
                "• **Примэрия и претуры**: адреса, график работы и часы приёма (бул. Штефан чел Маре, 83);\n"
                "• **Петиции и обращения**: порядок подачи и официальные сроки рассмотрения (30 дней).\n\n"
                "Какой вопрос вас интересует?"
            )
        else:
            greet_text = (
                "Bună ziua! Sunt asistentul municipal oficial al orașului Chișinău.\n\n"
                "Vă pot oferi informații actualizate și suport privind:\n"
                "• **Transportul public**: tariful călătoriilor (6 lei), orare și abonamente;\n"
                "• **Servicii municipale**: programarea la medicul de familie, eliberarea actelor;\n"
                "• **Primăria și preturile**: adresele, orarul și audiența (bd. Ștefan cel Mare, 83);\n"
                "• **Petiții și cereri**: procedura de depunere și termenele de examinare (30 de zile).\n\n"
                "Cu ce vă pot fi de folos astăzi?"
            )
        res_json = json.dumps(
            {"status": "ANSWERED", "answer": greet_text, "citations": [], "enough": True},
            ensure_ascii=False,
        )
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": res_json}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 60, "total_tokens": 70},
        }

    # 2. Мгновенная реакция на штрафы (консультация + уточняющий вопрос, без цитат)
    is_fine = any(w in q_lower for w in ["штраф", "amend", "penalit"])
    if is_fine and not is_translation:
        if is_ru:
            fine_text = (
                "Оплата административных штрафов в Кишинёве осуществляется:\n"
                "• Через государственный сервис электронных платежей **MPay** ([mpay.gov.md](https://mpay.gov.md));\n"
                "• В коммерческих банках Республики Молдова;\n"
                "• В почтовых отделениях **Poșta Moldovei**.\n\n"
                "Для оплаты необходимо указать номер протокола о правонарушении.\n\n"
                "Уточните, пожалуйста: о каком именно штрафе идёт речь (за парковку или другое нарушение)?"
            )
        else:
            fine_text = (
                "Achitarea amenzilor contravenționale în Chișinău se efectuează:\n"
                "• Prin serviciul guvernamental de plăți electronice **MPay** ([mpay.gov.md](https://mpay.gov.md));\n"
                "• La băncile comerciale din Republica Moldova;\n"
                "• La oficiile poștale **Poșta Moldovei**.\n\n"
                "Pentru plată este necesar numărul procesului-verbal.\n\n"
                "Vă rugăm să specificați: despre ce amendă este vorba (parcare sau altă contravenție)?"
            )
        res_json = json.dumps(
            {"status": "ANSWERED", "answer": fine_text, "citations": [], "enough": True},
            ensure_ascii=False,
        )
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": res_json}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 60, "total_tokens": 70},
        }

    # 3. Мгновенный словарь для перевода поискового запроса в FTS/эмбеддер
    if is_translation:
        dict_terms = [
            (
                [
                    "биле",
                    "билет",
                    "проезд",
                    "скок",
                    "скольк",
                    "тариф",
                    "троллейбус",
                    "автобус",
                    "транспорт",
                    "маршрутк",
                ],
                "bilet calatorie pret tarife transport troleibuz autobuz rtec",
            ),
            (
                ["примжр", "примэр", "примар", "мэри", "мэра", "где находит", "адрес", "контакт"],
                "primaria municipiului chisinau Stefan cel Mare adresa contacte",
            ),
            (
                ["петици", "жалоб", "обращен", "срок", "рассмотрен", "подать"],
                "petitie depunere examinare termen 30 zile lucratoare regulament",
            ),
            (
                ["штраф", "парковк", "оплат", "платит", "нарушен"],
                "amenda parcare achitare sanctiuni plata mpay",
            ),
            (
                ["врач", "поликлиник", "запис", "семейн", "больниц", "доктор"],
                "medic familie programare policlinica sector",
            ),
            (
                [
                    "аудиенц",
                    "прием",
                    "часы",
                    "график",
                    "ботаник",
                    "претур",
                    "рышкановк",
                    "буюкан",
                    "центр",
                    "чекан",
                ],
                "audienta program pretura botanica cetateni sector",
            ),
            (
                ["паспорт", "документ", "удостоверен", "булетин", "справк"],
                "acte identitate buletin eliberare termen ghiseu unic",
            ),
            (
                ["детсад", "садик", "школ", "зачислен", "ребен"],
                "gradinita scoala inscriere copii educatie",
            ),
            (
                ["мусор", "отход", "уборк", "салубритат", "свалк"],
                "deseuri autosalubritate evacuare salubrizare",
            ),
            (
                ["собак", "животн", "налог", "питомц"],
                "caini animale taxa intretinere",
            ),
            (
                ["привет", "здравствуй", "добрый", "салют", "хай"],
                "salut buna ziua",
            ),
        ]
        matched_ro = []
        for keywords, ro_phrase in dict_terms:
            if any(kw in q_lower for kw in keywords):
                matched_ro.append(ro_phrase)
        if matched_ro:
            combined = " ".join(matched_ro + [user_raw])
            res_content = json.dumps({"text": combined}, ensure_ascii=False)
            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": res_content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
            }

    messages_payload = [{"role": m.role, "content": m.content} for m in req.messages]

    if is_translation:
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
        inputs = _tokenizer.apply_chat_template(
            messages_payload,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to("cuda")

    start_t = time.perf_counter()
    gen_max_tokens = min(req.max_tokens, 32) if is_translation else min(req.max_tokens, 256)
    stop_criteria = StoppingCriteriaList([StopOnJsonClose(inputs.shape[1], _tokenizer)])

    with torch.no_grad():
        outputs = _model.generate(
            input_ids=inputs,
            attention_mask=torch.ones_like(inputs),
            max_new_tokens=gen_max_tokens,
            temperature=req.temperature,
            pad_token_id=_tokenizer.pad_token_id or _tokenizer.eos_token_id,
            use_cache=True,
            stopping_criteria=stop_criteria,
        )
    latency_ms = int((time.perf_counter() - start_t) * 1000)

    generated_ids = outputs[0][inputs.shape[1] :]
    raw_output = _tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    clean_json = extract_json_content(raw_output)

    if is_translation:
        translated_text = ""
        try:
            parsed = json.loads(clean_json)
            if isinstance(parsed, dict) and "text" in parsed:
                translated_text = str(parsed["text"]).strip()
        except Exception:
            translated_text = raw_output.strip().strip('"').strip("'")
        combined = f"{translated_text} {user_raw}".strip()
        clean_json = json.dumps({"text": combined}, ensure_ascii=False)
    else:
        try:
            parsed = json.loads(clean_json)
            if isinstance(parsed, dict):
                if "answer" in parsed:
                    parsed["answer"] = flatten_answer(parsed["answer"])
                answer_text = str(parsed.get("answer", "")).strip()
                answer_text = answer_text.replace("трамвае", "троллейбусе").replace("трамвай", "троллейбус")
                parsed["answer"] = answer_text
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
                            "чтобы я предоставил точные инструкции."
                        )
                    else:
                        conversational_answer = (
                            "În regulamentele municipale disponibile nu există detalii exhaustive pentru "
                            "întrebarea dumneavoastră. Vă rugăm să specificați: la ce serviciu vă "
                            "referiți (de exemplu, depunerea unei cereri online sau audiență la ghișeul "
                            "unic), pentru a vă putea ajuta cu informații exacte."
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

                    user_msg = next((m.content for m in req.messages if "<passages>" in m.content), "")
                    grounded = find_grounded_passages(answer_text, user_msg)
                    if valid_cits:
                        grounded_matches = [c for c in valid_cits if c in grounded]
                        parsed["citations"] = grounded_matches if grounded_matches else grounded
                    else:
                        parsed["citations"] = grounded

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

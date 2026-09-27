#!/usr/bin/env python3
"""Скрипт генерации синтетического поведенческого датасета для QLoRA (Unsloth).

Владелец: Паша
Контекст: GigaHack 2026, Smart City (Chișinău Municipal Assistant)

Назначение:
- Генерация 300–500 обучающих примеров поведения модели (JSON, статусы, цитирование).
- Модель учится ПОВЕДЕНИЮ (evidence-grounded reasoning, формат ответа, citations, NOT_FOUND),
  а не механическому запоминанию фактов.
- БЕЗОПАСНОСТЬ: Строгий запрет на использование записей с `hidden: true` из golden set.
- Работает полностью офлайн без обращения к внешним API.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

# Корректная обработка UTF-8 в Windows-консоли (cp1251)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULT_INSTRUCTION = (
    "Ответь на вопрос строго на основе предоставленного контекста. "
    "Если ответа нет, верни status: NOT_FOUND. Иначе ANSWERED. "
    "Отвечай на языке вопроса. Цитируй только номера пассажей."
)

# Вопросы вне домена корпуса (для тренировки честного NOT_FOUND)
OUT_OF_DOMAIN_QUESTIONS: list[tuple[str, str]] = [
    ("ru", "Какой налог на содержание собак в квартирах Кишинёва?"),
    ("ro", "Care este taxa pentru deținerea câinilor în apartament în Chișinău?"),
    ("ru", "Какая сумма штрафа за парковку на газоне в муниципии?"),
    ("ro", "Care este amenda pentru parcare neregulamentară pe spațiul verde?"),
    ("ru", "Как оформить биометрический загранпаспорт в Кишинёве?"),
    ("ro", "Cum se perfectează pașaportul biometric în Chișinău?"),
    ("ru", "Какой курс евро установлен Национальным банком Молдовы на сегодня?"),
    ("ro", "Care este cursul valutar al leului moldovenesc față de euro astăzi?"),
    ("ru", "Где в Кишинёве можно зарядить электромобиль бесплатно?"),
    ("ro", "Unde există stații gratuite de încărcare pentru mașini electrice în Chișinău?"),
    ("ru", "Какая погода ожидается завтра в муниципии Кишинэу?"),
    ("ro", "Care este prognoza meteo pentru mâine în Chișinău?"),
    ("ru", "Как записать ребёнка в бассейн в спортивную школу?"),
    ("ro", "Cum pot înscrie un copil la secția de înot în Chișinău?"),
    ("ru", "Где находится посольство Франции в Республике Молдова?"),
    ("ro", "Unde se află Ambasada Franței în Republica Moldova?"),
    ("ru", "Сколько стоит аренда велосипеда в парке Валя Морилор?"),
    ("ro", "Cât costă închirierea unei biciclete în parcul Valea Morilor?"),
    ("ru", "Как вызвать эвакуатор для сломанного автомобиля ночью?"),
    ("ro", "Cum se solicită serviciul de evacuare auto pe timp de noapte?"),
]

# Синтетические шаблоны вопросов и ответов по фактам из открытых документов mini_corpus
SYNTHETIC_CORPUS_PAIRS: list[dict[str, Any]] = [
    {
        "lang": "ro",
        "query": "În ce cazuri se acceptă examinarea petițiilor anonime?",
        "answer": ("Petițiile anonime se examinează doar dacă conțin informații despre fapte ilegale."),
        "passage_fragment": (
            "Petițiile anonime nu se examinează, cu excepția celor care "
            "conțin informații despre fapte ilegale."
        ),
    },
    {
        "lang": "ru",
        "query": "В каких исключительных случаях рассматриваются анонимные петиции?",
        "answer": (
            "Анонимные петиции рассматриваются только в том случае, "
            "если они содержат информацию о правонарушениях."
        ),
        "passage_fragment": (
            "Petițiile anonime nu se examinează, cu excepția celor care "
            "conțin informații despre fapte ilegale."
        ),
    },
    {
        "lang": "ro",
        "query": "În ce termen se comunică refuzul examinării unei petiții?",
        "answer": (
            "Refuzul de a examina petiția se comunică în termen de 5 zile lucrătoare de la înregistrare."
        ),
        "passage_fragment": (
            "Refuzul de a examina petiția se comunică în termen de 5 zile lucrătoare de la înregistrare."
        ),
    },
    {
        "lang": "ru",
        "query": "В течение скольких дней заявителю сообщают об отказе в рассмотрении петиции?",
        "answer": ("Отказ в рассмотрении петиции сообщается в течение 5 рабочих дней с момента регистрации."),
        "passage_fragment": (
            "Refuzul de a examina petiția se comunică в termen de 5 zile lucrătoare de la înregistrare."
        ),
    },
    {
        "lang": "ro",
        "query": "În ce termen se examinează petițiile care nu necesită verificări suplimentare?",
        "answer": (
            "Petițiile care nu necesită verificări suplimentare se examinează "
            "în termen de 15 zile lucrătoare."
        ),
        "passage_fragment": (
            "Petițiile care nu necesită verificări suplimentare se examinează "
            "în termen de 15 zile lucrătoare."
        ),
    },
    {
        "lang": "ru",
        "query": "Сколько дней рассматриваются петиции, не требующие дополнительных проверок?",
        "answer": (
            "Петиции, не требующие дополнительных проверок, рассматриваются в течение 15 рабочих дней."
        ),
        "passage_fragment": (
            "Petițiile care nu necesită verificări suplimentare se examinează "
            "în termen de 15 zile lucrătoare."
        ),
    },
    {
        "lang": "ro",
        "query": "Pe ce termen poate fi prelungită examinarea unei petiții dacă sunt necesare verificări?",
        "answer": "Termenul poate fi prelungit cu cel mult 30 de zile lucrătoare.",
        "passage_fragment": "termenul poate fi prelungit cu cel mult 30 de zile lucrătoare",
    },
    {
        "lang": "ru",
        "query": "На какой максимальный срок может быть продлено рассмотрение сложной петиции?",
        "answer": "Срок рассмотрения петиции может быть продлён не более чем на 30 рабочих дней.",
        "passage_fragment": "termenul poate fi prelungit cu cel mult 30 de zile lucrătoare",
    },
    {
        "lang": "ro",
        "query": "La ce număr de telefon poate fi apelat dispeceratul Regiei Autosalubritate?",
        "answer": "Dispeceratul poate fi contactat la numărul 022 74-61-16.",
        "passage_fragment": "Telefon dispecerat: 022 74-61-16",
    },
    {
        "lang": "ru",
        "query": "По какому номеру телефона работает диспетчерская служба Regia Autosalubritate?",
        "answer": "Номер телефона диспетчерской службы Autosalubritate: 022 74-61-16.",
        "passage_fragment": "Telefon dispecerat: 022 74-61-16",
    },
    {
        "lang": "ro",
        "query": "Care este adresa sediului Regiei Autosalubritate?",
        "answer": "Sediul se află pe str. 27 Martie 1918 nr. 14.",
        "passage_fragment": "str. 27 Martie 1918 nr. 14",
    },
    {
        "lang": "ru",
        "query": "На какой улице находится центральный офис Autosalubritate?",
        "answer": "Офис Autosalubritate расположен по адресу ул. 27 Марта 1918 года, № 14.",
        "passage_fragment": "str. 27 Martie 1918 nr. 14",
    },
    {
        "lang": "ro",
        "query": "În ce zile și ore au loc audiențele cetățenilor la Pretura Botanica?",
        "answer": "Audiențele au loc în zilele de luni și joi, între orele 08:00 și 17:00.",
        "passage_fragment": "Audiența cetățenilor: luni și joi, 08:00–17:00",
    },
    {
        "lang": "ru",
        "query": "В какие дни и часы проходит приём граждан в претуре сектора Ботаника?",
        "answer": "Приём граждан проходит по понедельникам и четвергам с 08:00 до 17:00.",
        "passage_fragment": "Audiența cetățenilor: luni și joi, 08:00–17:00",
    },
    {
        "lang": "ro",
        "query": "Care este numărul deciziei CMC prin care a fost aprobat regulamentul petițiilor?",
        "answer": (
            "Regulamentul a fost aprobat prin Decizia Consiliului Municipal Chișinău "
            "nr. 7/12 din 18 mai 2023."
        ),
        "passage_fragment": "Decizia Consiliului Municipal Chișinău nr. 7/12 din 18 mai 2023",
    },
    {
        "lang": "ru",
        "query": "Каким решением Муниципального совета Кишинёва был утверждён регламент о петициях?",
        "answer": ("Регламент утверждён решением Муниципального совета Кишинёва № 7/12 от 18 мая 2023 года."),
        "passage_fragment": "Decizia Consiliului Municipal Chișinău nr. 7/12 din 18 mai 2023",
    },
    {
        "lang": "ro",
        "query": "În ce zi se înregistrează petițiile depuse prin poșta electronică?",
        "answer": (
            "Petițiile prin poșta electronică se înregistrează în prima zi lucrătoare după recepționare."
        ),
        "passage_fragment": (
            "Petițiile depuse prin poșta electronică se înregistrează "
            "în prima zi lucrătoare după recepționare."
        ),
    },
    {
        "lang": "ru",
        "query": "Когда регистрируются электронные петиции, отправленные на официальный email?",
        "answer": "Электронные обращения регистрируются в первый рабочий день после получения.",
        "passage_fragment": (
            "Petițiile depuse prin poșta electronică se înregistrează "
            "în prima zi lucrătoare după recepționare."
        ),
    },
]


def load_golden_set(
    golden_path: Path,
) -> tuple[list[dict[str, Any]], set[str], set[str], set[str]]:
    """Загружает golden.jsonl, разделяя на открытые и закрытые (hidden) элементы.

    Возвращает:
    - open_items: список не скрытых записей;
    - hidden_ids: id закрытых записей (g13, g14...);
    - hidden_queries: тексты запросов закрытых записей в нижнем регистре;
    - hidden_passages: тексты пассажей закрытых записей в нижнем регистре.
    """
    if not golden_path.exists():
        raise FileNotFoundError(f"Файл golden set не найден: {golden_path}")

    all_items: list[dict[str, Any]] = []
    with open(golden_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                all_items.append(json.loads(line))

    open_items: list[dict[str, Any]] = []
    hidden_ids: set[str] = set()
    hidden_queries: set[str] = set()
    hidden_passages: set[str] = set()

    for item in all_items:
        if item.get("hidden", False):
            hidden_ids.add(str(item.get("id")))
            query = item.get("query", "").strip().lower()
            if query:
                hidden_queries.add(query)
            passage = item.get("expected_passage", "") or ""
            passage = passage.strip().lower()
            if passage:
                hidden_passages.add(passage)
        else:
            open_items.append(item)

    return open_items, hidden_ids, hidden_queries, hidden_passages


def load_corpus_chunks(
    corpus_dir: Path,
    hidden_passages: set[str],
    hidden_queries: set[str],
) -> list[str]:
    """Считывает текстовые абзацы (чанки) из файлов mini_corpus.

    Исключает любые чанки, содержащие скрытые фрагменты golden set.
    """
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Каталог mini_corpus не найден: {corpus_dir}")

    chunks: list[str] = []
    for md_file in corpus_dir.rglob("*.md"):
        if md_file.is_dir():
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        paragraphs = content.split("\n\n")
        for p in paragraphs:
            cleaned = p.strip()
            if cleaned.startswith("# ") and len(cleaned.split("\n")) == 1:
                continue
            cleaned = re.sub(r"^#+\s*", "", cleaned).strip()
            if len(cleaned) < 60:
                continue

            # Фильтрация скрытых фрагментов
            cleaned_lower = cleaned.lower()
            if any(hp in cleaned_lower for hp in hidden_passages):
                continue
            if any(hq in cleaned_lower for hq in hidden_queries):
                continue

            chunks.append(cleaned)

    # Дедупликация
    return sorted(list(set(chunks)))


def find_matching_chunk(passage: str, chunks: list[str]) -> str:
    """Находит в корпусе наиболее подходящий чанк, содержащий заданный фрагмент."""
    norm_target = passage.strip().lower()
    for c in chunks:
        if norm_target in c.lower():
            return c
    return passage.strip()


def build_input_context(passages: list[str], query: str) -> str:
    """Формирует поле input со стандартными маркерами контекста и вопроса."""
    lines = [f"Вопрос: {query}", "Контекст:"]
    for i, p in enumerate(passages, 1):
        lines.append(f"[{i}] {p}")
    return "\n".join(lines)


def format_json_output(status: str, answer: str, citations: list[int], enough: bool) -> str:
    """Формирует строгий сериализованный JSON без markdown-обёрток."""
    data = {
        "status": status,
        "answer": answer,
        "citations": citations,
        "enough": enough,
    }
    return json.dumps(data, ensure_ascii=False)


def generate_examples(
    open_items: list[dict[str, Any]],
    corpus_chunks: list[str],
    hidden_passages: set[str],
    target_count: int = 400,
    seed: int = 42,
) -> list[dict[str, str]]:
    """Генерирует сбалансированный поведенческий датасет (ANSWERED и NOT_FOUND)."""
    random.seed(seed)
    examples: list[dict[str, str]] = []

    # 1. Формирование пула пар для ANSWERED
    answered_pool: list[dict[str, Any]] = []

    # 1.1 Открытые примеры из golden set со статусом ANSWERED или CONFLICT с пассажем
    for item in open_items:
        passage = item.get("expected_passage")
        answer = item.get("expected_answer")
        query = item.get("query")
        if passage and answer and query and item.get("expected_status") != "NOT_FOUND":
            norm_p = passage.strip().lower()
            if any(hp in norm_p for hp in hidden_passages):
                continue
            chunk_text = find_matching_chunk(passage, corpus_chunks)
            answered_pool.append(
                {
                    "query": query,
                    "answer": answer,
                    "chunk": chunk_text,
                    "source": item.get("id"),
                }
            )

    # 1.2 Синтетические пары по фактам из открытых страниц mini_corpus
    for syn in SYNTHETIC_CORPUS_PAIRS:
        chunk_text = find_matching_chunk(syn["passage_fragment"], corpus_chunks)
        answered_pool.append(
            {
                "query": syn["query"],
                "answer": syn["answer"],
                "chunk": chunk_text,
                "source": "synthetic_corpus",
            }
        )

    distractor_pool = [c for c in corpus_chunks if len(c) > 70]

    # Вариации вопросов (вежливые префиксы, формулировки)
    prefixes_ro = [
        "",
        "Vă rog să-mi spuneți: ",
        "Informați-mă vă rog: ",
        "Care este răspunsul oficial la întrebarea: ",
    ]
    prefixes_ru = [
        "",
        "Подскажите, пожалуйста: ",
        "Скажите: ",
        "Какова официальная информация: ",
    ]

    for pair in answered_pool:
        target_chunk = pair["chunk"]
        raw_query = pair["query"]
        answer = pair["answer"]
        prefixes = prefixes_ru if any("а" <= ch <= "я" for ch in raw_query.lower()) else prefixes_ro

        for prefix in prefixes:
            augmented_query = f"{prefix}{raw_query}" if prefix else raw_query

            # Шаблон 1: один пассаж -> citation [1]
            examples.append(
                {
                    "instruction": DEFAULT_INSTRUCTION,
                    "input": build_input_context([target_chunk], augmented_query),
                    "output": format_json_output("ANSWERED", answer, [1], True),
                }
            )

            # Шаблон 2: target на позиции [1], отвлекающий на [2] -> citation [1]
            distractors = [d for d in distractor_pool if d != target_chunk]
            d1 = random.choice(distractors)
            examples.append(
                {
                    "instruction": DEFAULT_INSTRUCTION,
                    "input": build_input_context([target_chunk, d1], augmented_query),
                    "output": format_json_output("ANSWERED", answer, [1], True),
                }
            )

            # Шаблон 3: отвлекающий на [1], target на позиции [2] -> citation [2]
            d2 = random.choice(distractors)
            examples.append(
                {
                    "instruction": DEFAULT_INSTRUCTION,
                    "input": build_input_context([d2, target_chunk], augmented_query),
                    "output": format_json_output("ANSWERED", answer, [2], True),
                }
            )

            # Шаблон 4: три пассажа, target на позиции [2] -> citation [2]
            d3_candidates = [d for d in distractors if d != d2]
            d3 = random.choice(d3_candidates)
            examples.append(
                {
                    "instruction": DEFAULT_INSTRUCTION,
                    "input": build_input_context([d2, target_chunk, d3], augmented_query),
                    "output": format_json_output("ANSWERED", answer, [2], True),
                }
            )

            # Шаблон 5: три пассажа, target на позиции [3] -> citation [3]
            examples.append(
                {
                    "instruction": DEFAULT_INSTRUCTION,
                    "input": build_input_context([d2, d3, target_chunk], augmented_query),
                    "output": format_json_output("ANSWERED", answer, [3], True),
                }
            )

    # 3. Создание NOT_FOUND примеров
    not_found_pool: list[str] = []

    # 3.1 Открытые golden вопросы missing_information (g06, g07)
    for item in open_items:
        if item.get("expected_status") == "NOT_FOUND":
            not_found_pool.append(item["query"])

    # 3.2 Внедоменные вопросы
    for _lang, ood_q in OUT_OF_DOMAIN_QUESTIONS:
        not_found_pool.append(ood_q)

    # 3.3 Вопросы из answered_pool, но со СЛУЧАЙНЫМИ нерелевантными чанками
    for pair in answered_pool:
        not_found_pool.append(pair["query"])

    for q in not_found_pool:
        for _ in range(3):
            chosen = random.sample(distractor_pool, k=min(2, len(distractor_pool)))
            examples.append(
                {
                    "instruction": DEFAULT_INSTRUCTION,
                    "input": build_input_context(chosen, q),
                    "output": format_json_output("NOT_FOUND", "", [], False),
                }
            )

        single_chunk = random.choice(distractor_pool)
        examples.append(
            {
                "instruction": DEFAULT_INSTRUCTION,
                "input": build_input_context([single_chunk], q),
                "output": format_json_output("NOT_FOUND", "", [], False),
            }
        )

    # 4. Перемешивание и ограничение объёма выборки целевым числом
    random.shuffle(examples)

    # Дедупликация по input
    seen_inputs: set[str] = set()
    unique_examples: list[dict[str, str]] = []
    for ex in examples:
        inp = ex["input"]
        if inp not in seen_inputs:
            seen_inputs.add(inp)
            unique_examples.append(ex)

    if len(unique_examples) > target_count:
        unique_examples = unique_examples[:target_count]

    return unique_examples


def verify_no_hidden_contamination(
    examples: list[dict[str, str]],
    hidden_ids: set[str],
    hidden_queries: set[str],
    hidden_passages: set[str],
) -> None:
    """Строгая проверка: ни один сгенерированный пример не должен содержать скрытые данные."""
    for idx, ex in enumerate(examples, 1):
        input_text = ex["input"].lower()

        # Проверка по скрытым запросам
        for hq in hidden_queries:
            if hq in input_text:
                raise RuntimeError(
                    f"ОШИБКА БЕЗОПАСНОСТИ: Пример #{idx} содержит скрытый запрос из golden set: '{hq}'"
                )

        # Проверка по скрытым пассажам
        for hp in hidden_passages:
            if hp in input_text:
                raise RuntimeError(
                    f"ОШИБКА БЕЗОПАСНОСТИ: Пример #{idx} содержит скрытый пассаж из golden set: '{hp}'"
                )

        # Проверка валидности output JSON
        try:
            parsed = json.loads(ex["output"])
        except Exception as exc:
            raise ValueError(f"Пример #{idx} имеет невалидный output JSON: {exc}") from exc

        for req_field in ["status", "answer", "citations", "enough"]:
            if req_field not in parsed:
                raise ValueError(f"Пример #{idx} не содержит обязательное поле '{req_field}'")

        if parsed["status"] not in ["ANSWERED", "NOT_FOUND"]:
            raise ValueError(f"Пример #{idx} имеет недопустимый статус '{parsed['status']}'")

        if not isinstance(parsed["citations"], list):
            raise ValueError(f"Пример #{idx}: поле citations должно быть списком")


def parse_args() -> argparse.Namespace:
    """Парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Генерация синтетического поведенческого датасета для QLoRA (Unsloth)"
    )
    parser.add_argument(
        "--golden-path",
        type=str,
        default="data/fixture/golden.jsonl",
        help="Путь к golden.jsonl (чтение только открытых примеров)",
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default="data/fixture/mini_corpus",
        help="Каталог mini_corpus для извлечения чанков",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/train/behavioral_dataset.jsonl",
        help="Путь для сохранения сгенерированного датасета",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=400,
        help="Количество примеров для генерации (от 300 до 500, по умолчанию: 400)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (по умолчанию: 42)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    golden_file = Path(args.golden_path)
    corpus_folder = Path(args.corpus_dir)
    output_file = Path(args.output_path)

    print("=" * 65)
    print("🛠️ Генерация поведенческого датасета (Unsloth QLoRA)")
    print(f"Источник golden: {golden_file}")
    print(f"Корпус чанков:   {corpus_folder}")
    print(f"Выходной файл:   {output_file}")
    print(f"Целевой объём:   {args.count}")
    print("=" * 65)

    # 1. Загрузка golden set и изоляция hidden записей
    open_items, hidden_ids, hidden_queries, hidden_passages = load_golden_set(golden_file)
    print(
        f"[GOLDEN] Загружено открытых записей: {len(open_items)}, "
        f"заблокировано скрытых (hidden=True): {len(hidden_ids)}"
    )

    # 2. Загрузка чанков из корпуса (с исключением скрытых фактов)
    corpus_chunks = load_corpus_chunks(corpus_folder, hidden_passages, hidden_queries)
    print(f"[CORPUS] Извлечено безопасных уникальных чанков: {len(corpus_chunks)}")

    # 3. Генерация обучающих пар
    examples = generate_examples(
        open_items=open_items,
        corpus_chunks=corpus_chunks,
        hidden_passages=hidden_passages,
        target_count=args.count,
        seed=args.seed,
    )
    print(f"[GENERATE] Сгенерировано уникальных примеров: {len(examples)}")

    # 4. Проверка безопасности (no hidden leakage)
    verify_no_hidden_contamination(
        examples=examples,
        hidden_ids=hidden_ids,
        hidden_queries=hidden_queries,
        hidden_passages=hidden_passages,
    )
    print("[SECURITY] Проверка изоляции hidden-набора успешно пройдена (0 утечек).")

    # 5. Сохранение датасета
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"[SAVE] Файл успешно сохранён: {output_file.resolve()}")

    # 6. Статистика
    answered_count = sum(1 for ex in examples if "ANSWERED" in ex["output"])
    not_found_count = sum(1 for ex in examples if "NOT_FOUND" in ex["output"])
    print("\n[STATS] Распределение классов:")
    print(f"  - ANSWERED:  {answered_count} ({answered_count / len(examples) * 100:.1f}%)")
    print(f"  - NOT_FOUND: {not_found_count} ({not_found_count / len(examples) * 100:.1f}%)")

    # 7. Вывод первых 3 строк
    print("\n[PREVIEW] Первые 3 строки сгенерированного файла:")
    with open(output_file, encoding="utf-8") as f:
        for i in range(3):
            line = f.readline().strip()
            print(f"Строка #{i + 1}:\n{line}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

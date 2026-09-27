"""Генератор синтетического датасета поведения для QLoRA-адаптера (CONTEXT.md, раздел 11).

Дистиллирует текущий пайплайн (R1.retrieve → R2.rerank → L1.complete_json, те же SYSTEM/render_user,
что реально использует W1.ask) в тройки {system, user, target} для дообучения меньшей модели
(Gemma 3n E2B). Исключает документы, которые встречаются в golden-наборах по URL — иначе eval
на hidden (A/B "RAG+few-shot vs RAG+QLoRA") перестанет быть честным.

Требует настоящего "учителя": LLM=ollama|api с моделью посильнее той, что дообучаем.
Работает и на CORPUS=fixture (для smoke-теста пайплайна), но выдаст мало примеров — 14 документов.

uv run python scripts/gen_behavior_dataset.py --n 400 --out data/training/behavior_dataset.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from app.blocks import llm, rerank, retrieval, store
from app.blocks.workflow import prompts
from app.contracts.models import Lang, LLMAnswer
from pydantic import BaseModel


class _SyntheticQuestion(BaseModel):
    question: str


_QUESTION_SYSTEM: dict[Lang, str] = {
    "ro": (
        "Ești un cetățean din Chișinău. Pe baza textului de mai jos, formulează O întrebare scurtă și "
        "naturală, de tipul pe care ar pune-o cineva care caută exact acest răspuns pe site-ul primăriei. "
        "Răspunzi DOAR cu întrebarea, fără ghilimele și fără explicații."
    ),
    "ru": (
        "Ты житель Кишинёва. На основе текста ниже сформулируй ОДИН короткий естественный вопрос — "
        "такой, какой задал бы человек, ищущий именно этот ответ на сайте мэрии. "
        "Отвечай ТОЛЬКО вопросом, без кавычек и без пояснений."
    ),
}


def known_urls(*paths: Path) -> set[str]:
    """URL из golden-наборов — их нельзя брать как seed, иначе train и eval пересекутся."""
    urls: set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            url = item.get("expected_url")
            if url:
                urls.add(url)
    return urls


def synthesize_question(chunk_text: str, lang: Lang) -> str | None:
    result = llm.complete_json(_QUESTION_SYSTEM[lang], chunk_text, _SyntheticQuestion)
    return result.question.strip() if result else None


def make_example(question: str, lang: Lang) -> dict | None:
    """Прогоняет вопрос через настоящий R1→R2→L1 путь — тот же, что использует W1.ask."""
    query = retrieval.make_query(question, lang)
    candidates = retrieval.retrieve(query)
    top = rerank.rerank(query, candidates)
    if not rerank.is_enough(top):
        return None  # NOT_FOUND-примеры не нужны: гейт уже детерминирован, учить нечему

    system = prompts.SYSTEM[query.lang]
    user = prompts.render_user(query.text, top, query.lang)
    target = llm.complete_json(system, user, LLMAnswer)
    if target is None or not target.enough:
        return None
    return {"system": system, "user": user, "target": target.model_dump()}


def generate(n: int, exclude_urls: set[str], ru_share: float = 0.3, seed: int = 0) -> list[dict]:
    conn = store.connect()
    chunks = [c for c in store.get_chunks(conn, store.all_chunk_ids(conn)) if c.url not in exclude_urls]
    if not chunks:
        return []

    rng = random.Random(seed)
    rng.shuffle(chunks)

    examples: list[dict] = []
    seen_questions: set[str] = set()
    for chunk in chunks:
        if len(examples) >= n:
            break
        lang: Lang = "ru" if rng.random() < ru_share else "ro"
        question = synthesize_question(chunk.text, lang)
        if not question or question in seen_questions:
            continue
        example = make_example(question, lang)
        if example is None:
            continue
        seen_questions.add(question)
        examples.append(example)
    return examples


def main() -> int:
    parser = argparse.ArgumentParser(description="Генератор датасета поведения для QLoRA (CONTEXT.md §11)")
    parser.add_argument("--n", type=int, default=400)
    parser.add_argument("--out", type=Path, default=Path("data/training/behavior_dataset.jsonl"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--golden",
        type=Path,
        nargs="*",
        default=[Path("data/fixture/golden.jsonl"), Path("data/golden")],
        help="Файлы/папки golden.jsonl, которые нельзя пересекать по URL",
    )
    args = parser.parse_args()

    golden_files: list[Path] = []
    for p in args.golden:
        if p.is_dir():
            golden_files.extend(sorted(p.glob("*.jsonl")))
        elif p.suffix == ".jsonl":
            golden_files.append(p)

    examples = generate(args.n, known_urls(*golden_files), seed=args.seed)
    if not examples:
        print(
            "gen_behavior_dataset: 0 примеров — проверь LLM=ollama|api (учитель) и наполнение корпуса",
            file=sys.stderr,
        )
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"gen_behavior_dataset: {len(examples)} примеров → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

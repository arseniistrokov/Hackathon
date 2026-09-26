from __future__ import annotations

import logging
import re
from pathlib import Path

from app.config import settings
from app.contracts.models import EvalResult, GoldenItem

logger = logging.getLogger(__name__)

CJK_REGEX = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")


def load_golden(path: Path, hidden: bool | None = None) -> list[GoldenItem]:
    """Загрузить элементы golden из jsonl.

    hidden=True  -> только hidden
    hidden=False -> только open
    hidden=None  -> все
    """
    items: list[GoldenItem] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = GoldenItem.model_validate_json(line)
            if hidden is True and not item.hidden:
                continue
            if hidden is False and item.hidden:
                continue
            items.append(item)
    return items


def evaluate(items: list[GoldenItem], judge: bool = False) -> EvalResult:
    """Прогнать W1.ask по каждому элементу, посчитать N/M по метрикам и по категориям."""
    from app.blocks.workflow import ask

    total = len(items)
    recall_num, recall_den = 0, 0
    status_num, status_den = 0, total
    citation_num, citation_den = 0, 0
    lang_num, lang_den = 0, total
    by_category_counts: dict[str, list[int]] = {}
    failures: list[str] = []

    judge_num, judge_den = 0, 0
    can_judge = judge and (settings.LLM != "off")

    for item in items:
        # Инициализируем категорию
        cat_key = str(item.category)
        if cat_key not in by_category_counts:
            by_category_counts[cat_key] = [0, 0]
        by_category_counts[cat_key][1] += 1

        try:
            resp = ask(question=item.query, lang=item.lang)
        except Exception as e:
            logger.warning("Error calling ask for item %s: %s", item.id, e)
            failures.append(item.id)
            continue

        # 1. Status metric
        status_ok = resp.status == item.expected_status
        if status_ok:
            status_num += 1
            by_category_counts[cat_key][0] += 1

        # 2. Recall@5 metric (не считается для NOT_FOUND, знаменатель = элементы с expected_url)
        recall_ok = True
        if item.expected_status != "NOT_FOUND" and item.expected_url:
            recall_den += 1
            citation_urls = {c.url for c in resp.citations}
            recall_ok = item.expected_url in citation_urls
            if recall_ok:
                recall_num += 1

        # 3. Citation metric (не считается для NOT_FOUND, знаменатель = элементы с expected_passage)
        citation_ok = True
        if item.expected_status != "NOT_FOUND" and item.expected_passage:
            citation_den += 1
            citation_ok = any(item.expected_passage in (c.passage or "") for c in resp.citations)
            if citation_ok:
                citation_num += 1

        # 4. Language metric (язык совпадает, ответ не пустой при ANSWERED, без CJK)
        lang_match = resp.language == item.lang
        not_cjk = not bool(CJK_REGEX.search(resp.answer or ""))
        not_empty_if_answered = bool((resp.answer or "").strip()) if resp.status == "ANSWERED" else True
        lang_ok = lang_match and not_cjk and not_empty_if_answered
        if lang_ok:
            lang_num += 1

        # 5. Judge metric (только если judge=True и LLM != off)
        if can_judge:
            # Для L1 судьи
            judge_den += 1
            # Базовая проверка в L0: если ответ не пуст и ожидаемый ответ содержится
            if item.expected_answer and item.expected_answer.lower() in (resp.answer or "").lower():
                judge_num += 1

        # Проверка failures
        if not (status_ok and recall_ok and citation_ok and lang_ok):
            failures.append(item.id)

    answer_correct = (judge_num, judge_den) if can_judge else None

    return EvalResult(
        total=total,
        recall_at_5=(recall_num, recall_den),
        status_correct=(status_num, status_den),
        citation_correct=(citation_num, citation_den),
        language_correct=(lang_num, lang_den),
        answer_correct=answer_correct,
        by_category={k: (v[0], v[1]) for k, v in by_category_counts.items()},
        failures=failures,
    )


def format_table(result: EvalResult) -> str:
    """Форматировать результаты в виде таблицы без использования символа процента (%)."""
    lines: list[str] = [
        "================================================",
        "              EVALUATION REPORT                 ",
        "================================================",
        f"Total items evaluated: {result.total}",
        "------------------------------------------------",
        f"{'Metric':<25} | {'Score (N/M)':<15}",
        "------------------------------------------------",
        f"{'Recall@5':<25} | {result.recall_at_5[0]}/{result.recall_at_5[1]}",
        f"{'Status':<25} | {result.status_correct[0]}/{result.status_correct[1]}",
        f"{'Citation':<25} | {result.citation_correct[0]}/{result.citation_correct[1]}",
        f"{'Language':<25} | {result.language_correct[0]}/{result.language_correct[1]}",
    ]

    if result.answer_correct is not None:
        lines.append(f"{'Judge (Answer)':<25} | {result.answer_correct[0]}/{result.answer_correct[1]}")

    lines.append("------------------------------------------------")
    lines.append("By Category:")
    for cat, (num, den) in sorted(result.by_category.items()):
        lines.append(f"  - {cat:<23} : {num}/{den}")

    lines.append("------------------------------------------------")
    if result.failures:
        lines.append(f"Failures ({len(result.failures)}): " + ", ".join(result.failures))
    else:
        lines.append("Failures: None (all passed)")
    lines.append("================================================")

    return "\n".join(lines)

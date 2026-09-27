"""Блок W1 · workflow. Детерминированный проход: одна функция, фиксированный порядок шагов, без графов.

Контракт: docs/contracts/W1_workflow.md. Владелец: Арсений.
make_query → retrieve → rerank → evidence gate (CONFLICT | NOT_FOUND | ENOUGH)
→ generate → verify → AskResponse.
Модель цитаты не пишет: она выбирает номера passages, passage берётся из базы по id.
"""

from __future__ import annotations

import logging
import re
import time
import unicodedata
import uuid

from app.blocks import llm, rerank, retrieval, store
from app.config import settings
from app.contracts.models import (
    AskResponse,
    Citation,
    Conflict,
    Lang,
    LLMAnswer,
    Meta,
    Passage,
    Query,
)

from . import prompts

log = logging.getLogger(__name__)

# слова длиной ≥4, слишком частые в ro/ru, чтобы считаться сигналом пересечения при recovery
_STOPWORDS = {
    "este", "pentru", "care", "fost", "daca", "dacă", "spre", "catre",
    "către", "asupra", "acest", "acesta", "acestei", "aceste", "acele",
    "unde", "cand", "când", "dupa", "după", "intre", "între", "fara", "fără",
    "если", "этот", "эта", "это", "какой", "какая", "когда", "через",
    "более", "между", "также", "потому", "чтобы", "может", "нужно", "будет",
}

_WORD_RE = re.compile(r"[^\W\d_]{4,}", re.UNICODE)
_NUM_RE = re.compile(r"\d+")


def _strip_diacritics(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _word_tokens(text: str) -> set[str]:
    folded = _strip_diacritics(text.casefold())
    return {w for w in _WORD_RE.findall(folded) if w not in _STOPWORDS}


def _number_tokens(text: str) -> set[str]:
    return set(_NUM_RE.findall(text))


def recover_citations(answer: str, top: list[Passage]) -> list[Passage]:
    """Детерминированный откат, если LLMAnswer.citations пуст, а answer непустой и enough=true.

    Совпадение с фрагментом = лексическое пересечение нормализованных токенов (≥4 символа, без
    стоп-слов) не ниже CITATION_RECOVERY_MIN_OVERLAP ДОЛИ токенов ответа, ИЛИ общее число
    (год/сумма/срок и т.п.) между answer и фрагментом. Ни одного совпадения → пусто (NOT_FOUND).

    Среди совпавших оставляем не более CITATION_RECOVERY_MAX с наибольшим rerank-score (p.score),
    иначе при нескольких пересекающихся фрагментах (напр. старый и новый тариф) в цитаты попадают
    устаревшие источники только из-за лексического совпадения.
    """
    if not settings.CITATION_RECOVERY or not answer.strip():
        return []
    answer_words = _word_tokens(answer)
    answer_numbers = _number_tokens(answer)
    if not answer_words and not answer_numbers:
        return []

    matched: list[Passage] = []
    for p in top:
        passage_text = p.chunk.text
        overlap = answer_words & _word_tokens(passage_text)
        overlap_ratio = len(overlap) / len(answer_words) if answer_words else 0.0
        number_hit = bool(answer_numbers & _number_tokens(passage_text))
        if overlap_ratio >= settings.CITATION_RECOVERY_MIN_OVERLAP or number_hit:
            matched.append(p)
    matched.sort(key=lambda p: (-p.score, p.n))
    return matched[: settings.CITATION_RECOVERY_MAX]


def ask(question: str, lang: Lang | None = None) -> AskResponse:
    """Единая точка входа для POST /api/ask и eval.py."""
    t0 = time.perf_counter()
    query = retrieval.make_query(question, lang)
    cands = retrieval.retrieve(query)

    conn = None
    try:
        conn = store.connect()
        top = rerank.rerank(query, cands)
        conflicts = store.conflicts_for(conn, [p.chunk.id for p in top])

        if conflicts and not conflicts[0].resolved_by_date:
            return _conflict_response(conn, query, conflicts[0], len(cands), t0)
        if not rerank.is_enough(top):
            return _not_found_response(conn, query, len(cands), len(top), t0)
        return _answered_response(conn, query, top, conflicts, len(cands), t0)
    except Exception:  # noqa: BLE001 — любая ошибка после retrieve = NOT_FOUND, не 500
        log.warning("W1: ask failed after retrieve, falling back to NOT_FOUND", exc_info=True)
        if conn is None:
            conn = store.connect()
        return _not_found_response(conn, query, len(cands), 0, t0)
    finally:
        if conn is not None:
            conn.close()


def verify_citations(answer: LLMAnswer, passages: list[Passage]) -> list[Passage]:
    """Оставить только номера из retrieved-набора, без дублей, в порядке из answer. Пусто → NOT_FOUND."""
    by_n = {p.n: p for p in passages}
    seen: set[int] = set()
    used: list[Passage] = []
    for n in answer.citations:
        if n in by_n and n not in seen:
            used.append(by_n[n])
            seen.add(n)
    return used


def extractive_answer(passages: list[Passage], lang: Lang) -> LLMAnswer:
    """L0 без модели: ответ = текст лучшего passage, citations=[1], enough=True."""
    if not passages:
        return LLMAnswer(answer="", citations=[], enough=False)
    return LLMAnswer(answer=passages[0].chunk.text, citations=[1], enough=True)


def _answered_response(
    conn, query: Query, top: list[Passage], conflicts: list[Conflict], passages_retrieved: int, t0: float
) -> AskResponse:
    try:
        llm_answer = llm.complete_json(
            prompts.SYSTEM[query.lang], prompts.render_user(query.text, top, query.lang), LLMAnswer
        )
    except Exception:  # noqa: BLE001 — L1 обязан не падать сам, но W1 не доверяет соседям вслепую
        log.warning("W1: complete_json raised; falling back to extractive answer", exc_info=True)
        llm_answer = None
    if llm_answer is None:
        llm_answer = extractive_answer(top, query.lang)

    if not llm_answer.enough:
        return _not_found_response(conn, query, passages_retrieved, len(top), t0)

    used = verify_citations(llm_answer, top)
    citation_source = "model"
    if not used:
        used = recover_citations(llm_answer.answer, top)
        citation_source = "recovered"
    if not used:
        return _not_found_response(conn, query, passages_retrieved, len(top), t0)

    citations = [_to_citation(p) for p in used]
    warning = None
    if conflicts and conflicts[0].resolved_by_date:
        stale = conflicts[0].b
        date_text = stale.date.isoformat() if stale.date else ""
        warning = prompts.WARNING_STALE_SOURCE[query.lang].format(url=stale.citation.url, date=date_text)

    navigation = store.site_navigation(conn, citations[0].site)
    query_id = uuid.uuid4().hex[:12]
    meta = _meta(conn, passages_retrieved, len(top), query_id, t0)
    meta.citation_source = citation_source
    store.save_query(
        conn,
        query_id=query_id,
        question=query.text,
        lang=query.lang,
        status="ANSWERED",
        answer=llm_answer.answer,
        chunk_ids=[c.chunk_id for c in citations],
        model=meta.model,
        latency_ms=meta.latency_ms,
    )
    return AskResponse(
        question=query.text,
        language=query.lang,
        status="ANSWERED",
        answer=llm_answer.answer,
        citations=citations,
        warning=warning,
        navigation=navigation,
        meta=meta,
    )


def _conflict_response(
    conn, query: Query, conflict: Conflict, passages_retrieved: int, t0: float
) -> AskResponse:
    query_id = uuid.uuid4().hex[:12]
    answer = prompts.CONFLICT_ANSWER[query.lang]
    citations = [conflict.a.citation, conflict.b.citation]
    meta = _meta(conn, passages_retrieved, 0, query_id, t0)
    store.save_query(
        conn,
        query_id=query_id,
        question=query.text,
        lang=query.lang,
        status="CONFLICT",
        answer=answer,
        chunk_ids=[c.chunk_id for c in citations],
        model=meta.model,
        latency_ms=meta.latency_ms,
    )
    return AskResponse(
        question=query.text,
        language=query.lang,
        status="CONFLICT",
        answer=answer,
        citations=citations,
        conflict=conflict,
        meta=meta,
    )


def _not_found_response(
    conn, query: Query, passages_retrieved: int, passages_used: int, t0: float
) -> AskResponse:
    query_id = uuid.uuid4().hex[:12]
    meta = _meta(conn, passages_retrieved, passages_used, query_id, t0)
    store.save_query(
        conn,
        query_id=query_id,
        question=query.text,
        lang=query.lang,
        status="NOT_FOUND",
        answer="",
        chunk_ids=[],
        model=meta.model,
        latency_ms=meta.latency_ms,
    )
    return AskResponse(question=query.text, language=query.lang, status="NOT_FOUND", answer="", meta=meta)


def _meta(conn, passages_retrieved: int, passages_used: int, query_id: str, t0: float) -> Meta:
    stats = store.stats(conn)
    return Meta(
        corpus_documents=stats.corpus_documents,
        corpus_chunks=stats.corpus_chunks,
        passages_retrieved=passages_retrieved,
        passages_used=passages_used,
        model=llm.model_name(),
        latency_ms=int((time.perf_counter() - t0) * 1000),
        query_id=query_id,
    )


def _to_citation(p: Passage) -> Citation:
    c = p.chunk
    return Citation(
        chunk_id=c.id,
        document_id=c.document_id,
        title=c.title,
        url=c.url,
        site=c.site,
        section=c.section,
        page=c.page,
        passage=c.text,
        date=c.date,
    )

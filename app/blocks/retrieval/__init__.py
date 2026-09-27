"""Блок R1 · retrieval. Гибридный поиск: FTS5 (D1) + косинус по numpy-матрице → RRF → top-N.

Контракт: docs/contracts/R1_retrieval.md. Владелец: Арсений.
EMBEDDER=hash   → детерминированные char-ngram эмбеддинги (без модели, L0).
EMBEDDER=bge-m3 → sentence-transformers BAAI/bge-m3 (extra ml, L1); ошибка → откат на hash.
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np

from app.blocks import llm, store
from app.config import settings
from app.contracts.models import Chunk, Lang, Passage, Query

from . import l0

log = logging.getLogger(__name__)

_EXPECTED_DIM = {"hash": 2048, "bge-m3": 1024}
_RRF_K = 60

_index_cache: dict[str, tuple[list[str], np.ndarray, list[str]]] = {}

# Словарный фолбэк для ru→ro (R2 hotfix): дообученная API-модель (qwen2.5-3b-qlora) на
# llm.l1.translate не переводит, а возвращает почти неизменный (по многим разным вопросам —
# один и тот же) набор ключевых слов категории, из-за чего FTS/rerank не находят реальный
# документ. Для частотных бытовых терминов подставляем точную ro-форму напрямую — детерминированно,
# без сети. Ключ — русская основа (без окончаний), матчится подстрокой по casefold-тексту вопроса.
_RU_RO_TERMS: dict[str, str] = {
    "петици": "petiție",
    "врач": "medic",
    "троллейбус": "troleibuz",
    "налог": "impozit",
    "парковк": "parcare",
    "свадьб": "căsătorie",
    "брак": "căsătorie",
    "детсад": "grădiniță",
    "мусор": "gunoi deșeuri",
    "вода": "apă",
    "отоплени": "încălzire",
}


def _dictionary_translate(text: str) -> str | None:
    """Подстрочный ru→ro фолбэк по _RU_RO_TERMS. Пусто, если ни один термин не встретился."""
    folded = text.casefold()
    hits = [ro for stem, ro in _RU_RO_TERMS.items() if stem in folded]
    if not hits:
        return None
    return " ".join(dict.fromkeys(hits))  # без дублей, порядок стабилен (порядок _RU_RO_TERMS)


def _ro_prefix(translated: str) -> str:
    """Модель (qwen2.5-3b-qlora) часто дописывает исходный ru-вопрос кириллицей после ro-ответа
    (иногда ещё и в JSON-обвязке) — берём только "чистый" ro-префикс до первой кириллицы/`{`/`"`.
    """
    if not translated:
        return ""
    cut = len(translated)
    for i, ch in enumerate(translated):
        if ("а" <= ch.lower() <= "я") or ch.lower() == "ё" or ch in "{\"":
            cut = i
            break
    return translated[:cut].strip()


def make_query(text: str, lang: Lang | None = None) -> Query:
    """detect_lang (L1) → для ru: search_text = translate(text, 'ro').

    LLM=api (единственная реальная эксплуатационная конфигурация с моделью, вызывающей сеть):
    llm.l1.translate у дообученной под другую задачу модели (qwen2.5-3b-qlora) неустойчив — часто
    возвращает один и тот же набор категорийных слов независимо от вопроса и дописывает исходный
    ru-текст кириллицей после ro-ответа (см. _ro_prefix). Поэтому для частотных бытовых терминов
    сначала пробуем словарный фолбэк _RU_RO_TERMS (точная ro-форма, не размывает lexical rerank
    лишними словами), а "грязный" перевод модели чистим до ro-префикса. LLM=off/ollama — поведение
    не меняется (identity / translate как есть), чтобы не сломать существующий контракт R1.

    Категория — если роутер уверен, иначе None.
    """
    resolved_lang = lang or llm.detect_lang(text)
    search_text = text
    if resolved_lang == "ru":
        if settings.LLM == "api":
            dict_hit = _dictionary_translate(text)
            search_text = dict_hit or (_ro_prefix(llm.translate(text, "ro")) or text)
        else:
            search_text = llm.translate(text, "ro")
    return Query(
        text=text,
        lang=resolved_lang,
        search_text=search_text,
        category=l0.detect_category(search_text),
    )


def embed(texts: list[str]) -> np.ndarray:
    """float32 [len(texts), dim], L2-нормировано. Одинаковые тексты → одинаковые векторы."""
    if settings.EMBEDDER == "bge-m3":
        try:
            from . import l1

            return l1.embed(texts)
        except Exception:  # noqa: BLE001 — любая ошибка L1 = откат на hash, не падение
            log.warning("R1: bge-m3 embedder failed, falling back to hash", exc_info=True)
    return l0.embed(texts)


def retrieve(query: Query, n: int | None = None) -> list[Passage]:
    """top-N кандидатов (settings.TOP_N) с RRF-скором и sources. Нумерация n=1.. по убыванию скора."""
    top_n = n or settings.TOP_N
    conn = store.connect()
    try:
        fts_ids = [
            chunk_id
            for chunk_id, _ in store.fts_search(conn, query.search_text, k=top_n, category=query.category)
        ]
        vec_ids = _vector_candidates(conn, query.search_text, query.category, top_n)

        scores = _rrf_scores(fts_ids, vec_ids)
        if not scores:
            return []

        ranked_ids = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
        chunks_by_id = {chunk.id: chunk for chunk in store.get_chunks(conn, ranked_ids)}
        ranked_ids = [chunk_id for chunk_id in ranked_ids if chunk_id in chunks_by_id][:top_n]

        fts_set, vec_set = set(fts_ids), set(vec_ids)
        passages: list[Passage] = []
        for rank, chunk_id in enumerate(ranked_ids, start=1):
            sources: list[Literal["fts", "vec"]] = []
            if chunk_id in fts_set:
                sources.append("fts")
            if chunk_id in vec_set:
                sources.append("vec")
            passages.append(
                Passage(
                    n=rank,
                    chunk=chunks_by_id[chunk_id],
                    score=round(scores[chunk_id], 6),
                    sources=sources,
                )
            )
        return passages
    finally:
        conn.close()


def build_index() -> int:
    """Посчитать эмбеддинги для всех chunks из D1 и сохранить через D1.save_embeddings.

    Вернуть число строк.
    """
    conn = store.connect()
    try:
        ids = store.all_chunk_ids(conn)
        chunks = store.get_chunks(conn, ids)
    finally:
        conn.close()
    matrix = embed([chunk.text for chunk in chunks])
    store.save_embeddings(ids, matrix, settings.EMB_PATH)
    _index_cache.pop(settings.EMBEDDER, None)
    return len(ids)


def _rrf_scores(fts_ids: list[str], vec_ids: list[str]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for rank, chunk_id in enumerate(fts_ids, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (_RRF_K + rank)
    for rank, chunk_id in enumerate(vec_ids, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (_RRF_K + rank)
    return scores


def _vector_candidates(conn, text: str, category: str | None, top_n: int) -> list[str]:
    ids, matrix, categories = _load_index(conn)
    if not ids:
        return []
    query_vec = embed([text])[0]
    if query_vec.shape[0] != matrix.shape[1]:
        log.warning(
            "R1: query embedding dim %d != index dim %d; skipping vector search",
            query_vec.shape[0],
            matrix.shape[1],
        )
        return []
    sims = matrix @ query_vec
    order = sorted(range(len(ids)), key=lambda i: (-float(sims[i]), ids[i]))
    if category is not None:
        order = [i for i in order if categories[i] == category]
    return [ids[i] for i in order[:top_n]]


def _load_index(conn) -> tuple[list[str], np.ndarray, list[str]]:
    """Кэш на процесс, ключ — текущий EMBEDDER (переключение уровня строит индекс заново)."""
    cache_key = settings.EMBEDDER
    cached = _index_cache.get(cache_key)
    if cached is not None:
        return cached

    ids_all = store.all_chunk_ids(conn)
    if not ids_all:
        result: tuple[list[str], np.ndarray, list[str]] = ([], np.zeros((0, 0), dtype=np.float32), [])
        _index_cache[cache_key] = result
        return result

    chunks_by_id = {chunk.id: chunk for chunk in store.get_chunks(conn, ids_all)}
    persisted = store.load_embeddings(settings.EMB_PATH)
    expected_dim = _EXPECTED_DIM.get(cache_key)

    if persisted is not None:
        ids, matrix = persisted
        if matrix.ndim == 2 and matrix.shape[0] == len(ids) and matrix.shape[1] == expected_dim:
            categories = [_category_of(chunks_by_id, chunk_id) for chunk_id in ids]
            result = (ids, matrix, categories)
            _index_cache[cache_key] = result
            return result
        log.warning(
            "R1: persisted embeddings dim mismatch for embedder=%s; vector search disabled", cache_key
        )
        result = ([], np.zeros((0, 0), dtype=np.float32), [])
        _index_cache[cache_key] = result
        return result

    matrix = embed([chunks_by_id[chunk_id].text for chunk_id in ids_all])
    categories = [chunks_by_id[chunk_id].category for chunk_id in ids_all]
    result = (ids_all, matrix, categories)
    _index_cache[cache_key] = result
    return result


def _category_of(chunks_by_id: dict[str, Chunk], chunk_id: str) -> str:
    chunk = chunks_by_id.get(chunk_id)
    return chunk.category if chunk is not None else ""

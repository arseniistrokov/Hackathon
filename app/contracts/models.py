"""Общие модели контрактов. ТОЛЬКО ЧТЕНИЕ для всех блоков.

Меняют только Арсений и Никита отдельным PR `contracts/<что>` в dev.
Блоки общаются друг с другом исключительно этими моделями. Свои копии/версии заводить нельзя.

Поток данных:
  RawPage (I1 fetch) → Chunk (I2 chunker) → SQLite + .npy (D1 store)
  Query → Passage[] (R1 retrieval) → Passage[] с score (R2 rerank) → AskResponse (W1 workflow)
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["ro", "ru"]
Status = Literal["ANSWERED", "NOT_FOUND", "CONFLICT"]

# Категории сайтов Annex 1. Ключи — как в data/sites.yaml. Фильтр retrieval и группировка скаута.
CATEGORIES = ("transparency", "mobility", "urban", "education", "health", "districts", "services", "other")


# ----------------------------------------------------------------------------- ingestion
class RawPage(BaseModel):
    """Одна страница (или один PDF), как её сохранил блок I1 в data/raw/<site>/<slug>.md + .meta.json."""

    site: str  # ключ из data/sites.yaml, например "rtec.md"
    url: str
    title: str
    text: str  # markdown/plain после trafilatura или pymupdf; без навигации и футеров
    category: str  # одно из CATEGORIES
    lang: Lang = "ro"
    date: dt.date | None = None  # дата документа/публикации, если источник её отдаёт (WP REST, trafilatura)
    kind: Literal["html", "pdf"] = "html"
    fetched_at: dt.datetime | None = None


class Chunk(BaseModel):
    """Единица retrieval и цитирования. id детерминирован: sha1(url + section + порядковый номер)[:16]."""

    id: str
    document_id: str  # sha1(url)[:16] — один документ = много chunks
    site: str
    category: str
    url: str
    title: str
    section: str | None = None  # заголовок h2/h3, «Articolul 14» для PDF
    page: int | None = None  # только для PDF
    text: str = Field(min_length=1)
    lang: Lang = "ro"
    date: dt.date | None = None
    content_hash: str  # sha1(text) — чтобы переиндексация не плодила дубли


# ----------------------------------------------------------------------------- retrieval
class Query(BaseModel):
    """Вопрос после detect_lang и (для ru) перевода на ro для лексического поиска."""

    text: str  # оригинал, как ввёл пользователь
    lang: Lang
    search_text: str  # текст для FTS5/эмбеддинга: для ru — перевод на ro (блок L1), для ro — оригинал
    category: str | None = None  # если роутер уверен; иначе None = искать везде


class Passage(BaseModel):
    """Chunk с оценками. Номер `n` (1..K) — то, что видит модель и на что она ссылается в citations."""

    n: int
    chunk: Chunk
    score: float  # после R2 — скор reranker'а 0..1; после R1 — RRF (только для отладки)
    sources: list[Literal["fts", "vec"]] = []  # каким поиском найден; для meta и отладки


# ----------------------------------------------------------------------------- answer
class Citation(BaseModel):
    """Passage берётся из базы по chunk_id. Модель цитаты не пишет — она выбирает номер."""

    chunk_id: str
    document_id: str
    title: str
    url: str
    site: str
    section: str | None = None
    page: int | None = None
    passage: str  # дословный текст chunk — гарантированно есть в корпусе по построению
    date: dt.date | None = None


class ConflictSide(BaseModel):
    citation: Citation
    value: str  # «6 lei», «08:00–17:00»
    date: dt.date | None = None


class Conflict(BaseModel):
    """Два источника в корпусе говорят разное про одну сущность. Ищется офлайн (S1), хранится в SQLite."""

    id: str
    entity: str  # «тариф на проезд в троллейбусе», «часы приёма претуры Botanica»
    a: ConflictSide
    b: ConflictSide
    resolved_by_date: bool = False  # обе даты есть и разные → ANSWERED + предупреждение, иначе CONFLICT


class Navigation(BaseModel):
    label: str
    url: str


class Meta(BaseModel):
    corpus_documents: int  # размер корпуса, а не «просмотрено 42»
    corpus_chunks: int
    passages_retrieved: int  # сколько кандидатов вернул R1
    passages_used: int  # сколько прошло reranker и попало в модель
    model: str  # "extractive" на L0, иначе имя модели
    latency_ms: int
    query_id: str  # для /feedback


class LLMAnswer(BaseModel):
    """Схема, по которой модель обязана ответить (ollama format / json_schema). Ничего кроме этого."""

    answer: str = Field(description="Ответ на языке вопроса. Только факты из passages.")
    citations: list[int] = Field(
        default_factory=list, description="Номера passages [n], на которых основан ответ"
    )
    enough: bool = Field(description="false, если в passages нет ответа на вопрос")


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    lang: Lang | None = None  # None → detect_lang


class AskResponse(BaseModel):
    """Контракт POST /api/ask. Фронт (U1) стартует с data/fixture/mock_responses/*.json ровно этой формы."""

    question: str
    language: Lang
    status: Status
    answer: str  # NOT_FOUND → пусто; CONFLICT → короткое объяснение, что источники расходятся
    citations: list[Citation] = []
    conflict: Conflict | None = None
    # ANSWERED с устаревшим вторым источником: «документ X от <дата> говорит иначе»
    warning: str | None = None
    navigation: Navigation | None = None
    meta: Meta


class FeedbackRequest(BaseModel):
    query_id: str
    rating: Literal[1, -1]
    comment: str = Field(default="", max_length=2000)


class Stats(BaseModel):
    """GET /api/stats — для футера фронта и слайда."""

    corpus_documents: int
    corpus_chunks: int
    sites: int
    conflicts: int
    queries: int
    feedback_up: int
    feedback_down: int
    model: str


# ----------------------------------------------------------------------------- eval
GoldenCategory = Literal[
    "normal_ro",
    "normal_ru",
    "ru_question_ro_doc",
    "missing_information",
    "contradiction",
    "exact_citation",
    "navigation",
    "multi_document",
]


class GoldenItem(BaseModel):
    """Одна строка data/fixture/golden.jsonl (и data/golden/*.jsonl). Пишут дизайнеры + Арсений (G1)."""

    id: str
    query: str
    lang: Lang
    category: GoldenCategory
    expected_status: Status
    expected_answer: str | None = None  # для судьи; NOT_FOUND → None
    expected_url: str | None = None  # документ, который обязан быть в citations (Recall@5 считается по url)
    expected_passage: str | None = None  # подстрока, которая обязана быть в одной из citations.passage
    hidden: bool = False  # hidden 10: никогда в few-shot, никогда в промпте, только в eval


class EvalResult(BaseModel):
    """Что печатает eval.py. Числа — как N/M, не проценты (на слайд тоже N/M)."""

    total: int
    recall_at_5: tuple[int, int]
    status_correct: tuple[int, int]
    citation_correct: tuple[int, int]
    language_correct: tuple[int, int]
    answer_correct: tuple[int, int] | None = None  # только с судьёй (L1)
    by_category: dict[str, tuple[int, int]] = {}
    failures: list[str] = []  # id golden-элементов, где что-то не сошлось

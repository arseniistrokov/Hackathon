# Референсы D1 · SQLite + FTS5 + матрица эмбеддингов

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
# app/blocks/store/__init__.py — сигнатуры уже в файле, тела заменить
def connect() -> sqlite3.Connection                       # CORPUS=fixture → :memory: из data/fixture/mini_corpus (через I1.load_raw + I2.chunk); real → DB_PATH
def init_schema(conn) -> None                            # CREATE TABLE IF NOT EXISTS …; chunks_fts: FTS5, tokenize='unicode61 remove_diacritics 2', content=chunks
def upsert_document(conn, page: RawPage, document_id: str) -> None
def upsert_chunks(conn, chunks: list[Chunk]) -> int        # по id; content_hash тот же → пропуск; возвращает число новых
def get_chunks(conn, ids: list[str]) -> list[Chunk]        # в порядке ids
def all_chunk_ids(conn) -> list[str]                      # ORDER BY rowid — порядок строк матрицы
def fts_search(conn, query: str, k=20, category=None) -> list[tuple[str, float]]   # (chunk_id, bm25), лучшие первыми; слова через OR; спецсимволы FTS экранированы
def save_embeddings(ids, matrix: np.ndarray, path: Path) -> None   # float32, L2-норм; рядом <path>.ids.json
def load_embeddings(path) -> tuple[list[str], np.ndarray] | None
def insert_conflict(conn, conflict: Conflict) -> None
def conflicts_for(conn, chunk_ids: list[str]) -> list[Conflict]
def save_query(conn, query_id, question, lang, status, answer, chunk_ids, model, latency_ms) -> None
def save_feedback(conn, query_id, rating: int, comment: str) -> None
def site_navigation(conn, site: str) -> Navigation | None  # из site_pages, заполняется из data/sites.yaml (contact → services → url)
def stats(conn) -> Stats
def document_date(conn, document_id: str) -> date | None
```
Схема (минимум): `documents(id PK, site, url UNIQUE, title, category, lang, date, kind, fetched_at)`; `chunks(id PK, document_id, site, category, url, title, section, page, text, lang, date, content_hash)`; `chunks_fts` (FTS5 над `text`, `title`, `section`); `conflicts(id PK, entity, a_chunk, b_chunk, a_value, b_value, a_date, b_date, resolved_by_date)`; `queries(id PK, ts, question, lang, status, answer, chunk_ids JSON, model, latency_ms)`; `feedback(id, query_id, rating, comment, ts)`; `site_pages(site PK, label, contact, services, url)`.
Fixture-режим: `connect()` при `CORPUS=fixture` строит базу в памяти ОДИН раз на процесс (кэш на уровне модуля) из `data/fixture/mini_corpus` и `data/sites.yaml`; пока I1/I2 не готовы — используй `_patterns/backend_block/fixture_loader.py` (чтение md + meta.json и наивная нарезка по `## `). После их приёмки — заменить на порты I1/I2.

Переключатель уровня: `CORPUS=fixture|real`. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/blocks/store/__init__.py` — порт с `NotImplementedError`: тела заменить, сигнатуры оставить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `connect()` на fixture: `stats().corpus_documents == expect.documents`, `corpus_chunks ≥ documents × expect.min_chunks_per_page`, `sites == expect.sites`.
2. `fts_search(conn, 'petitie termen')` (без диакритики!) находит chunk с `expect.petition_term_passage` в top-3; то же для `'petiție termen'`.
3. `fts_search(conn, 'troleibuz tarif', category='mobility')` возвращает только chunks с `category == 'mobility'`.
4. `fts_search` с кавычками, `*`, `AND`, `"` и пустой строкой не бросает исключение (пустая → `[]`).
5. `upsert_chunks` дважды на одном списке → второй раз возвращает 0 и число строк не растёт.
6. `get_chunks(ids)` возвращает в порядке `ids`, неизвестные id пропускает.
7. `save_embeddings` + `load_embeddings` round-trip: те же ids, та же матрица, `dtype float32`.
8. `insert_conflict` + `conflicts_for([a_chunk])` и `conflicts_for([b_chunk])` оба находят конфликт; `conflicts_for([])` → `[]`.
9. `site_navigation(conn, 'autosalubritate.md')` == `expect.navigation['autosalubritate.md']`; для сайта без contact/services → `url` из sites.yaml; неизвестный сайт → `None`.
10. `save_query` + `save_feedback` + `stats()`: `queries == 1`, `feedback_up == 1`.

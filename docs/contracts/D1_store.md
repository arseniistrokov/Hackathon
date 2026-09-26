# D1 · SQLite + FTS5 + матрица эмбеддингов

> **Контракт блока.** Вставь этот файл целиком в нейронку. Работай строго по нему. Контекст проекта — `docs/CONTEXT.md`.

| | |
|---|---|
| Блок | `D1` · `store` · группа DATA |
| Владелец | **Никита** |
| Запасной | Арсений |
| Первое ревью | Арсений |
| Одобряет merge | Арсений (не автор PR) |
| Ветка | `feat/D1-<кратко>` → PR в `dev` |
| Зависит от | I2 |
| Кто использует | R1, W1, A1, S1, E1 |

## Инструкция для нейронки-планировщика (ChatGPT / Claude / Qwen)
Ты — **планировщик** блока `D1`. Код ты не пишешь: код пишет CLI-агент (Claude Code / Codex / Antigravity) по твоим задачам. Человек между вами — Никита: он копирует твои задачи агенту и присылает тебе результат.

**Первый ответ.** Разбей уровень **L0** на 5–9 задач и выдай ДОСКУ (формат ниже). Требования к задаче:
- начинается с глагола, помещается в 2 строки, делается агентом за ≤ 45 минут;
- трогает только файлы из «Разрешённых путей»;
- у каждой есть **проверка** — команда или тест, по которому видно, что готово;
- первая задача — всегда тесты на критерии приёмки (они сначала красные).

**Дальше — по одной задаче.** Выдавай задачу N как готовый промпт для агента:
```
ЗАДАЧА D1-N: <что сделать>
ФАЙЛЫ: <список из разрешённых путей>
ПРОВЕРКА: <команда / тест>
НЕ ДЕЛАТЬ: <что вне этой задачи>
```
Следующую задачу давай только после моего сообщения `готово N` + вывод проверки. Проверка красная → сначала чини, задачу не закрывай. Я написал `стоп` или `блокер` → зафиксируй ❌ с причиной и предложи обход в рамках путей блока или скажи, кому написать (владелец файла, Арсений).

**Каждый твой ответ заканчивается доской целиком** — я копирую её в `docs/status/D1.md` без правок:
```
## Доска D1 · уровень L0
| # | Задача | Статус | Проверка |
|---|--------|--------|----------|
| 1 | ... | ✅ | uv run pytest tests/blocks/... -q |
| 2 | ... | ⏳ | ... |
| 3 | ... | ☐ | ... |
Блокеры: — | <кто нужен и зачем>
Обновлено: <дата время>
```
Статусы: `☐` не начато · `⏳` в работе · `✅` проверка зелёная · `❌` блокер. Все ✅ → выдай `ЗАДАЧА D1-QA` по разделу «QA перед PR» (все пункты списком, агент выполняет сам). Получил QA-отчёт со всеми ✅ или с ❌ вне путей блока → напиши «L0 готов, открывай PR» и выдай отчёт по шаблону в конце контракта. К L1 переходи только по моему сообщению `L0 принят`.

## Цель
Единственное место в проекте, где есть SQL. Один файл SQLite: documents, chunks, chunks_fts (FTS5), conflicts, feedback, queries, site_pages. Эмбеддинги — numpy-матрица в `.npy` + список id рядом; векторная БД не нужна (20k × 1024 float32 = 80 МБ, косинус брутфорсом — миллисекунды).

## Разрешённые пути
Можно создавать и менять ТОЛЬКО эти файлы:
- `app/blocks/store/**`
- `tests/blocks/store/**`
- `docs/status/D1.md` — доска задач блока

## Порт (что блок обязан предоставить)
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

## Модели контрактов, которые использует блок
Импорт: `from app.contracts.models import ...` (фронт — `frontend/src/api/types.ts`, зеркало). Не менять, не копировать.
```python
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
```
## Уровни (заменяемость)
| Уровень | Что сделать |
|---|---|
| **L0** | `:memory:` из fixture. Всё, кроме `save_embeddings/load_embeddings`, работает без numpy-файла. |
| **L1** | `CORPUS=real` → файл `DB_PATH`, WAL, индексы; `scripts/index.py` наполняет базу через порты I1 → I2 → D1 → R1.build_index → S1. |
| **L2** | Инкрементальная переиндексация по `content_hash`. |

Переключатель: `CORPUS=fixture|real`

## Зависимости, которыми можно пользоваться (уже установлены)
`sqlite3` (stdlib), `numpy`, `pyyaml`

## Критерии приёмки
Ссылки вида `expect.*` — это `data/fixture/expect.json`.
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

## Запрещено
- SQL вне этого блока.
- Векторная БД, sqlite-vec, любые расширения SQLite кроме встроенного FTS5.
- ORM.

## Референсы (фиксированы)
Папка `docs/references/D1/` — образцы структуры и стиля кода для этого блока и общие шаблоны `docs/references/_patterns/`. Агент пишет код по ним и **не предлагает свою архитектуру, библиотеки или раскладку файлов**. Референс противоречит контракту → контракт главнее, расхождение — в отчёт.

## QA перед PR (делает агент, не человек)
Это отдельная задача `ЗАДАЧА D1-QA`, её выдаёт планировщик после того, как все задачи уровня ✅. Делает CLI-агент, а не человек. Каждый пункт — выполнить и записать результат. Найденную проблему агент чинит сам в своих путях (максимум 2 попытки на проблему), после починки прогоняет весь список заново. Не смог починить или проблема вне своих путей → ❌ с описанием в QA-отчёт, PR всё равно открывается.

**1. Критерии приёмки, по одному.** Для каждого критерия из раздела «Критерии приёмки»: назвать тест, который его закрывает, и показать, что он зелёный. Критерий без теста → написать тест. Тест, который проходит и при сломанной реализации → переписать.
**2. Мутационная проверка.** Сломать реализацию тремя способами (вернуть константу; поменять знак/порядок сравнения; выбросить исключение внутри L1) → тесты обязаны покраснеть каждый раз. Не покраснели → тесты слабые, усилить. Реализацию вернуть.
**3. Границы данных.** Прогнать порт на: пустом списке; одном элементе; дубликатах id; `None` в опциональных полях; строках с пробелами, другим регистром и без диакритики (`ș/ş`, `ț/ţ`, `ă`); текстах на ru и ro вперемешку. Падение или неожиданный результат → починить + тест.
**4. Откат на L0.** Выставить переключатель уровня в L1 и подменить L1 исключением/таймаутом (monkeypatch) → порт возвращает результат L0, в логе warning, наружу ничего не летит.
**5. Детерминированность.** Два вызова подряд на одних данных → одинаковый результат, включая порядок элементов в списках.
**6. Границы блока.** `python3 scripts/check_paths.py D1` зелёный. `git diff --stat` не содержит замороженных файлов (`app/contracts/models.py`, `app/config.py`, `app/main.py`, `app/api/router.py`, `data/fixture/**`, `pyproject.toml`, `uv.lock`, `frontend/package.json`, lock-файлы). Соседние блоки импортированы только через их `__init__`.
**7. Чистота кода.** `grep -rn "print(\|TODO\|FIXME\|XXX" <свои пути>` пусто (кроме CLI `__main__.py`, где `print` — вывод пользователю). Нет закомментированного кода. Нет мёртвых функций. Нет классов-фабрик, плагинов и абстракций «на будущее». Типы у всех сигнатур.
**8. Тесты без сети.** Отключить сеть (или `monkeypatch` на `httpx`, чтобы любой вызов бросал) → все тесты блока зелёные. Ключи и `.env` в тестах не читаются: тесты работают на значениях по умолчанию из `app/config.py`.
**9. Размер PR.** `git diff --stat dev...HEAD -- ':!*test*'` ≤ 250 строк. Больше → сказать человеку, как разбить.

**10. Линтер.** `uv run ruff check app tests scripts` чисто; `uv run ruff format --check app tests scripts` чисто.
**11. Полный прогон.** `uv run pytest -q` по всему репо зелёный: мой блок не сломал соседей и `tests/test_fixture_valid.py`.
**12. Fixture не подогнан.** `git diff data/fixture/` пуст. `expect.json` не редактировался.

QA-отчёт — в `docs/status/D1.md` под доской, формат:
```
QA D1 · уровень L0 · <дата время>
Пункты: 1 ✅ · 2 ✅ (3/3 мутации покраснели) · 3 ✅ · 4 ✅ · 5 ✅ · 6 ✅ · 7 ✅ · 8 ✅ · 9 ✅ (147 строк) · 10 ✅ · 11 ❌ · 12 ✅
Найдено и починено: <кратко, по пунктам>
Не починено: 11 — <что именно, почему, кому нужно>
Добавлено тестов: <N>
```

## Общие правила (одинаковы для всех блоков)
1. **Трогай только файлы из раздела «Разрешённые пути».** Нужно изменить что-то вне списка — ОСТАНОВИСЬ и напиши владельцу этого файла. CI отклонит PR, который вышел за свои пути.
2. **Модели из `app/contracts/models.py` не менять и не копировать.** Только импортировать. Не хватает поля — остановись, напиши Арсению.
3. **Сначала уровень L0, отдельным PR.** Только после его приёмки — L1.
4. **Переключатель уровня — переменная окружения** из раздела «Уровни» (`app/config.py`, `.env`). По умолчанию всегда L0. Любая ошибка L1 (сеть, ключ, таймаут, исключение, модель не установлена) → тихий откат на L0 и запись в лог, а не падение.
5. **Внешние вызовы:** таймаут явно (HTTP ≤ 10 с, LLM ≤ `LLM_TIMEOUT_S`), максимум 1 повтор. В тестах сеть запрещена: тесты проходят без интернета, без моделей и без ключей.
6. **Все библиотеки из раздела «Зависимости» уже в `pyproject.toml`.** Модели (`sentence-transformers`, `torch`) — extra `ml`, импортируются только внутри `l1.py` и только лениво (внутри функции), чтобы L0 работал без них. Файлы `pyproject.toml`, `uv.lock`, `frontend/package.json` НЕ трогай. Нужна другая библиотека — остановись и спроси.
7. **SQL только в блоке D1.** Вызов модели только в блоке L1. Регистрация роутов в `app/api/router.py` — только C0.
8. **Тесты обязательны** и лежат в пути из контракта. Каждый критерий приёмки = минимум один тест. Данные для тестов — только `data/fixture/` (не выдумывай свои).
9. **Размер PR ≤ 250 строк** без учёта тестов. Больше — дели на части.
10. Один файл на модуль, без классов-фабрик, без плагинов, без абстракций «на будущее». Без `print` (кроме CLI), без закомментированного кода, без TODO. Типы везде. `ruff check` чистый.

## Порядок работы
1. Вставь этот файл целиком в чат-нейронку. Она работает по «Инструкции для планировщика» и выдаёт доску задач.
2. Копируй задачи по одной в CLI-агент. Смотри diff: файл вне «Разрешённых путей» — откати.
3. Запусти проверку из задачи сам, пришли вывод планировщику: `готово N` + вывод. Доску из ответа сохрани в `docs/status/D1.md` и закоммить вместе с кодом.
4. Все ✅ → планировщик выдаёт `ЗАДАЧА D1-QA`, агент проходит раздел «QA перед PR» сам, чинит найденное и пишет QA-отчёт в `docs/status/D1.md`. Ты QA не делаешь — только читаешь его отчёт.
5. QA пройден → агент дописывает «Отчёт» в `docs/status/D1.md` по шаблону ниже и ставит ✅ уровню в `docs/team/Никита.md`. Открой PR в `dev`, тот же отчёт — в чат. Следующий уровень — только после `L0 принят`.

## Отчёт (в `docs/status/D1.md` и в чат)
```
БЛОК: <id> · УРОВЕНЬ: L0 | L1
ВЕТКА: feat/<id>-<кратко>  →  PR в: dev
ИЗМЕНЁННЫЕ ФАЙЛЫ: <список>
ТЕСТЫ: <вывод pytest / tsc — последние строки>
КРИТЕРИИ ПРИЁМКИ: [x] 1  [x] 2  [ ] 3 — <почему не выполнен>
QA: <N>/<M> пунктов ✅ · не починено: <номера или «нет»> · добавлено тестов: <N>
ВЫШЕЛ ЗА РАЗРЕШЁННЫЕ ПУТИ: нет | да — <что и зачем>
ВОПРОСЫ / БЛОКЕРЫ: <или «нет»>
```

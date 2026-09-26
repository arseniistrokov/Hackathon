# Референсы R1 · Гибридный поиск: FTS5 + numpy косинус → RRF

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`
- `docs/references/_patterns/llm_call/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
def make_query(text: str, lang: Lang | None = None) -> Query    # lang or detect_lang; ru → search_text = translate(text,'ro'); category — по словарю ключевых слов, только если ≥ 2 совпадения одной категории и 0 других, иначе None
def embed(texts: list[str]) -> np.ndarray                         # float32 [n, dim], L2-норм
def retrieve(query: Query, n: int | None = None) -> list[Passage] # settings.TOP_N; RRF(k=60) по спискам fts (D1.fts_search) и vec (косинус по D1.load_embeddings); sources заполнены; n=1.. по убыванию
def build_index() -> int                                          # embed(all chunks) → D1.save_embeddings(EMB_PATH)
```
L0 `embed` (EMBEDDER=hash): hashing-trick по символьным 3-граммам без диакритики и в нижнем регистре, dim=2048, L2-норма. Детерминировано, без модели. Достаточно, чтобы тесты на fixture проходили и чтобы пайплайн работал без GPU.
L1 (EMBEDDER=bge-m3): `SentenceTransformer('BAAI/bge-m3')`, ленивый импорт внутри `l1.py`, `normalize_embeddings=True`, батч 32. Нет модели / нет torch → warning + откат на hash (и тогда индекс надо пересобрать тем же эмбеддером: в `<EMB_PATH>.ids.json` хранится имя эмбеддера, несовпадение → vec-список пуст, работает только FTS).
Если матрицы нет (fixture-режим до `build_index`) — `retrieve` строит её в памяти один раз на процесс.

Переключатель уровня: `EMBEDDER=hash|bge-m3`. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/blocks/retrieval/__init__.py` — порт с `NotImplementedError`: тела заменить, сигнатуры оставить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `retrieve(make_query('Care este termenul de examinare a petiției?'))` содержит chunk с `expect.petition_term_passage` в top-5 (fixture, L0).
2. `retrieve(make_query('Cât costă o călătorie cu troleibuzul?'))` содержит chunks из `expect.tariff_new_url` и `expect.tariff_old_url` в top-10.
3. `make_query('Какой срок рассмотрения петиции?')` → `lang == 'ru'`; при `translate` замоканном на румынский перевод `search_text` — перевод; при `LLM=off` — оригинал.
4. `embed(['a', 'a'])` — две одинаковые строки; `embed([])` → форма `(0, dim)`; нормы строк ≈ 1.
5. Каждый `Passage` имеет непустой `sources`; chunk, найденный обоими поисками, имеет RRF-скор выше, чем найденный одним (при прочих равных рангах).
6. `n=1..len` без пропусков и в порядке убывания `score`; дубликатов `chunk.id` нет.
7. `query.category='mobility'` → все passages `category == 'mobility'`.
8. При `EMBEDDER=bge-m3` и отсутствии `sentence_transformers` (monkeypatch импорта) `embed` работает через hash, без исключения.

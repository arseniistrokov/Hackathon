# Референсы R2 · Reranker = механизм NOT_FOUND

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`
- `docs/references/_patterns/llm_call/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
def rerank(query: Query, passages: list[Passage], k: int | None = None) -> list[Passage]   # settings.TOP_K; score 0..1; n=1..K; стабильная сортировка (при равных — по исходному n)
def is_enough(passages: list[Passage]) -> bool          # passages and passages[0].score >= settings.RERANK_THRESHOLD
```
L0 (RERANKER=lexical): токены запроса и passage → нижний регистр, диакритика снята (`unicodedata` NFKD без combining, плюс `ș→s`, `ț→t`), стоп-слова ro/ru убраны; score = |общие токены| / |токены запроса|, при этом сравнивается `query.search_text` (для ru — перевод) И `query.text` — берётся максимум.
L1 (RERANKER=bge): `CrossEncoder('BAAI/bge-reranker-v2-m3')`, ленивый импорт, `predict([(query.search_text, p.chunk.text)])`, сигмоида → 0..1. Ошибка/нет модели → откат на lexical + warning.
Порог `RERANK_THRESHOLD` калибруется по golden set через E1 (в субботу днём), не «на глаз». Для lexical и bge пороги разные — в `.env`.

Переключатель уровня: `RERANKER=lexical|bge`, `RERANK_THRESHOLD`. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/blocks/rerank/__init__.py` — порт с `NotImplementedError`: тела заменить, сигнатуры оставить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. На fixture: для вопроса про petiție passage с `expect.petition_term_passage` — первый после `rerank`, `is_enough` → True.
2. Для `expect.not_found_queries` (парковочные штрафы и т. п.) при passages из `R1.retrieve` `is_enough` → False на L0 с порогом по умолчанию.
3. `rerank` возвращает ≤ K, `n=1..K`, скор невозрастающий, все `0 ≤ score ≤ 1`; пустой вход → `[]`; `is_enough([])` → False.
4. `petitie` без диакритики и `petiție` с диакритикой дают одинаковый lexical-скор.
5. Два вызова → одинаковый порядок (стабильность при равных скорах).
6. При `RERANKER=bge` и исключении в l1 (monkeypatch) → результат lexical, warning в логе, без исключения.

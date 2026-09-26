# Референсы E1 · Eval: цифра до любого тюнинга

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`
- `docs/references/_patterns/llm_call/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
def load_golden(path: Path, hidden: bool | None = None) -> list[GoldenItem]
def evaluate(items: list[GoldenItem], judge: bool = False) -> EvalResult
def format_table(result: EvalResult) -> str
```
Метрики (по одному вызову `W1.ask` на элемент):
- `recall_at_5`: `expected_url` есть среди `citations[].url` ИЛИ среди url passages, попавших в модель (для этого `W1.ask` кладёт использованные chunk_ids в `meta`? — нет: считать по `citations`, а для NOT_FOUND-элементов метрика не считается, знаменатель = элементы с `expected_url`);
- `status_correct`: `status == expected_status`;
- `citation_correct`: `expected_passage` — подстрока одной из `citations[].passage` (знаменатель — элементы с `expected_passage`);
- `language_correct`: `language == lang` и ответ не пустой при ANSWERED и не содержит CJK-символов;
- `answer_correct` (только `judge=True`): `L1.complete_json` со схемой `Verdict(correct: bool, reason: str)`; `LLM=off` → `None`;
- `by_category`: `status_correct` по `GoldenCategory`.
`failures` — id элементов, где хоть одна метрика не сошлась. CLI печатает таблицу и список failures с ожидаемым/полученным статусом. `--hidden` — только hidden; по умолчанию — только open (hidden никогда не в промптах и не в few-shot).

Переключатель уровня: —. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/blocks/eval/__init__.py` — порт с `NotImplementedError`: тела заменить, сигнатуры оставить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `load_golden(fixture)` → `expect.golden_total`; `hidden=True` → `expect.golden_hidden`; `hidden=False` → разница.
2. `evaluate` с monkeypatch `W1.ask` на идеальный ответ (строится из golden) → все метрики `N/N`, `failures == []`.
3. `evaluate` с `W1.ask`, всегда возвращающим NOT_FOUND → `status_correct` равен числу элементов с `expected_status == NOT_FOUND`, остальные в `failures`.
4. `format_table` содержит строки `Recall@5`, `Status`, `Citation`, `Language` в формате `N/M` и ни одного символа `%`.
5. `evaluate(judge=True)` при `LLM=off` → `answer_correct is None`, не падает.
6. Элемент с `expected_status == NOT_FOUND` не входит в знаменатель `recall_at_5` и `citation_correct`.

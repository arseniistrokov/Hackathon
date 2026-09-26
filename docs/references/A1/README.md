# Референсы A1 · Роуты /feedback и /stats

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
POST /api/feedback  {query_id, rating: 1|-1, comment}  → 201 {"status": "saved"}; неизвестный query_id → 404
GET  /api/stats                                        → Stats (D1.stats + model из L1.model_name())
```
Роуты ничего не считают: только валидация (pydantic уже делает), вызов порта, код ответа.

Переключатель уровня: —. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/api/routes/feedback.py` — гнездо роута: тело заменить
- `app/api/routes/stats.py` — гнездо роута: тело заменить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `POST /api/feedback` c существующим `query_id` (создать через `D1.save_query` в тесте) → 201; неизвестный → 404; `rating=0` → 422.
2. `GET /api/stats` → 200, `corpus_documents == expect.documents`, `model == 'extractive'` при `LLM=off`.
3. `GET /api/health` → 200 (уже есть; тест на всякий случай).
4. `POST /api/ask` с пустым `question` → 422 (валидация каркаса; тест, что роут жив, с monkeypatch порта W1).

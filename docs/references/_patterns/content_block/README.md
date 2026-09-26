# Образец контент-блока (G1, P1 — дизайнеры)

Здесь нет кода. Здесь — как выписывать так, чтобы по этому можно было мерить.

## Golden-вопрос (одна строка `data/golden/golden.jsonl`)
```json
{"id": "g_rtec_001", "query": "Cât costă o călătorie cu troleibuzul?", "lang": "ro", "category": "normal_ro",
 "expected_status": "ANSWERED", "expected_answer": "6 lei", "expected_url": "https://rtec.md/<точный адрес страницы>",
 "expected_passage": "<фраза, скопированная со страницы дословно, ≤ 120 символов, с диакритикой как на сайте>", "hidden": false}
```
Правила:
- `query` — как спросил бы гражданин, не как написано на сайте. К каждому RO-вопросу по RO-странице — RU-вариант с `category: ru_question_ro_doc`.
- `expected_url` — адрес именно той страницы, где фраза. Не главная страница сайта.
- `expected_passage` — Ctrl+C со страницы. Не пересказ. Проверить, что подстрока есть в тексте страницы (Ctrl+F).
- `missing_information` — вопрос, на который ответа в корпусе точно нет (проверить поиском по сайтам): `expected_status: NOT_FOUND`, `expected_url: null`, `expected_passage: null`.
- `contradiction` — вопрос под найденную конфликтную пару: `expected_status: CONFLICT` (даты нет) или `ANSWERED` с новым документом (даты есть).
- `hidden: true` — у 10 вопросов. Их никому не показывать, в чат не кидать, в промпты не вставлять.
- Образец с 16 строками: `data/fixture/golden.jsonl` (это выдуманные данные для тестов, не копировать факты).

## Конфликтная пара (`data/conflicts_manual.json`)
```json
[{"id": "cf_<кратко>", "entity": "<что именно расходится>", "entity_kind": "tariff|hours|deadline|phone|address|decision",
  "a": {"url": "...", "quote": "<дословно со страницы A>", "value": "6 lei", "date": "2024-07-01"},
  "b": {"url": "...", "quote": "<дословно со страницы B>", "value": "2 lei", "date": null},
  "resolved_by_date": false}]
```
Где искать: тарифы (rtec vs chisinau.md), часы приёма претур (сайт претуры vs help.chisinau.md / chisinau.md), сроки (регламент vs страница услуги), телефоны (страница контактов vs футер другого сайта). `date` — только если на странице явно есть дата документа/публикации.

## Страницы навигации (`data/sites.yaml`, поля `label`, `contact`, `services`)
Для каждого сайта волны 1: `contact` — страница с телефоном/адресом; `services` — страница со списком услуг/регламентов. Только эти три поля; остальное правит Никита.

## Проверка
`uv run python scripts/validate_data.py` (структура) и `--online` (URL отвечают). Красное → починить до PR.

# Fixture — общие тестовые данные для всех блоков

**Всё здесь выдумано.** Страницы, тарифы, телефоны, сроки и решения — синтетические тестовые данные,
похожие на настоящие муниципальные сайты Кишинёва, но не взятые с них. Не цитировать как факты.

Только чтение: тесты всех блоков работают на этих файлах, менять их может только Арсений отдельным PR.
`expect.json` — эталон, под свой код его не подгонять.

## Что лежит

| Путь | Что | Кто читает |
|---|---|---|
| `mini_corpus/<site>/<slug>.md` + `<slug>.meta.json` | 14 страниц (10 RO, 4 RU, 1 PDF-подобная) — ровно то, что блок I1 `save_raw` кладёт в `data/raw/` | I1 `load_raw`, I2, D1 (CORPUS=fixture) |
| `golden.jsonl` | 16 строк `GoldenItem`, все 8 категорий, 4 `hidden=true` | E1 eval, W1 тесты |
| `conflicts.json` | 2 ручные конфликтующие пары (формат ниже) | S1 `load_manual`, W1 |
| `expect.json` | эталонные числа и URL для assert'ов | все тесты |
| `mock_responses/*.json` | 5 валидных `AskResponse` — по одному на каждое состояние экрана | U1/U2 фронт (`VITE_USE_MOCK`), A1 |

`meta.json` = поля `RawPage` без `text`: `site, url, title, category, lang, date, kind, fetched_at`. `text` — содержимое `.md`.

## Что в корпусе зашито специально

- **Срок петиции** (`regulament-petitii.pdf`, Articolul 14, только RO) — вопрос по-русски должен найти румынский документ.
- **Датированный конфликт**: rtec.md 2024 «6 lei» vs chisinau.md 2021 «2 lei» → `ANSWERED` + `warning` (`resolved_by_date=true`).
- **Недатированный конфликт**: botanica.md «08:00–17:00» vs help.chisinau.md «09:00–16:00», обе без даты → `CONFLICT`.
- **NOT_FOUND**: нигде нет штрафов за парковку и налога на собак — тест это проверяет grep-ом.
- **multi_document**: срок грантов e-tineret есть и в RO-, и в RU-версии страницы.

## Формат `conflicts.json`

Chunk id считает блок I2, поэтому ручные пары ссылаются на chunk через `(url, quote)`:

```json
{"id": "cf_tariff", "entity": "tarif călătorie troleibuz", "entity_kind": "tariff",
 "a": {"url": "...", "quote": "<дословная подстрока chunk>", "value": "6 lei", "date": "2024-07-01"},
 "b": {"url": "...", "quote": "...", "value": "2 lei", "date": "2021-03-10"},
 "resolved_by_date": true}
```

S1 `load_manual` находит chunk по `url` + вхождению `quote` в `chunks.text` (D1) и собирает `Conflict` из моделей контрактов.
Тот же формат — у `data/conflicts_manual.json`, который дизайнеры (G1) заполняют по реальному корпусу.

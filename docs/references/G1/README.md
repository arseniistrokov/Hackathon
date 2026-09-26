# Референсы G1 · Golden set, конфликтная пара, страницы навигации

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/content_block/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```
data/golden/golden.jsonl          30–40 строк GoldenItem (формат — data/fixture/golden.jsonl как образец); hidden: true у 10
data/conflicts_manual.json        ≥ 1 настоящая пара, формат — data/fixture/conflicts.json (url + дословная quote + value + date)
data/sites.yaml                   у каждого сайта первой волны заполнены label, contact, services (только эти поля!)
```
Как выписывать: открыть страницу → вопрос, который реально задаст гражданин (RO и RU варианты) → `expected_answer` одной фразой → `expected_url` — точный адрес страницы → `expected_passage` — скопированная дословно фраза ≤ 120 символов (с диакритикой как на сайте) → категория. На каждый сайт первой волны ≥ 3 вопроса. Обязательно: ≥ 3 `missing_information` (ответа в корпусе точно нет), ≥ 2 `contradiction`, ≥ 5 `ru_question_ro_doc`, ≥ 2 `navigation`, ≥ 2 `multi_document`.
Проверка: `uv run python scripts/validate_data.py` (валидность строк, уникальные id, распределение категорий, доступность URL).

Переключатель уровня: —. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `data/golden/**` — данные; образец формата в `data/fixture/`
- `data/sites.yaml` — данные; образец формата в `data/fixture/`
- `data/conflicts_manual.json` — данные; образец формата в `data/fixture/`

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `scripts/validate_data.py` зелёный: все строки валидны, id уникальны, `hidden` ровно 10 (L1) / ≥ 4 (L0).
2. Каждый `expected_passage` — дословная подстрока страницы по `expected_url` (проверено открытием страницы).
3. Есть ≥ 1 пара в `data/conflicts_manual.json` с реальными URL и дословными цитатами; значения расходятся.
4. У всех сайтов `wave: 1` заполнены `label`, `contact`, `services`.
5. Hidden-вопросы не пересказаны нигде в `docs/` и не показаны команде в чате.

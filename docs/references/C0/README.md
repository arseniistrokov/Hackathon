# Референсы C0 · Каркас проекта

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`
- `docs/references/_patterns/frontend_feature/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
Результат — не функция, а состояние репозитория:
- `uv sync && uv run pytest -q` зелёный на чистом клоне, без сети и без моделей;
- `app/contracts/models.py`, `app/config.py`, `app/main.py`, `app/api/router.py` — заморожены;
- для КАЖДОГО блока создан пакет `app/blocks/<name>/__init__.py` с функциями из его контракта, которые бросают `NotImplementedError("<ID>")`;
- роуты `/api/ask`, `/api/feedback`, `/api/stats`, `/api/health` зарегистрированы;
- `data/fixture/`: mini_corpus (14 страниц), golden.jsonl (16), conflicts.json, expect.json, mock_responses;
- `frontend/` собирается (`npm run build`) и показывает три состояния с моков;
- `scripts/check_paths.py`, `scripts/gen_contracts.py`, `scripts/index.py`, `scripts/validate_data.py`, CI, pre-commit.

Переключатель уровня: —. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `data/fixture/**` — данные; образец формата в `data/fixture/`
- `data/sites.yaml` — данные; образец формата в `data/fixture/`

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `uv run pytest -q` зелёный на чистом клоне.
2. `grep -rn NotImplementedError app/blocks` показывает гнездо для каждого блока I1, I2, D1, S1, R1, R2, L1, W1, E1; `app/api/routes/feedback.py`, `stats.py` — для A1.
3. `cd frontend && npm run build` проходит.
4. `python scripts/gen_contracts.py` идемпотентен: повторный запуск не меняет файлы.

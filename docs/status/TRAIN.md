# Статус TRAIN · QLoRA-обучение и поведенческий датасет (Qwen2.5-3B-Instruct)

Владелец: Паша · Задачи: `TRAIN-QLORA`, `TRAIN-DATASET`  
Контекст: GigaHack 2026, Smart City (Chișinău Municipal Assistant)  
Железо: NVIDIA GeForce RTX 3080 Ti (12GB VRAM)

## Доска TRAIN
| # | Задача | Статус | Проверка |
|---|--------|--------|----------|
| 1 | Создание скрипта `scripts/qlora_train.py` | ✅ | `uv run ruff check scripts/qlora_train.py` |
| 2 | Создание каталога сохранения адаптера `models/qlora_adapter/` | ✅ | `Test-Path models/qlora_adapter` |
| 3 | Защита от утечки `data/golden/**` в обучение | ✅ | `python scripts/qlora_train.py --data-path data/golden/...` → ValueError |
| 4 | Проверка импорта Unsloth и подсказка по установке | ✅ | `python scripts/qlora_train.py` → вывод понятной ошибки и команды установки |
| 5 | Оптимизации под 12GB VRAM (4-bit QLoRA, adamw_8bit, gradient checkpointing) | ✅ | параметры `load_in_4bit=True`, `batch_size=1`, `grad_accum=8`, `max_seq_length=2048` |
| 6 | Скрипт генерации датасета `scripts/generate_behavioral_dataset.py` | ✅ | `uv run ruff check scripts/generate_behavioral_dataset.py` |
| 7 | Генерация датасета `data/train/behavioral_dataset.jsonl` (300–500 примеров) | ✅ | `python scripts/generate_behavioral_dataset.py` → 400 валидных записей |
| 8 | Аппаратная изоляция hidden-примеров golden set | ✅ | `verify_no_hidden_contamination` → 0 утечек |
| 9 | QLoRA-дообучение модели `unsloth/Qwen2.5-3B-Instruct` (3 эпохи, 150 шагов) | ✅ | Финальный loss: 0.051, сохранён `adapter_model.safetensors` (120 МБ) |

Блокеры: —  
Обновлено: 2026-09-27 03:37

## Поведенческий датасет (TRAIN-DATASET)
- **Принцип:** Датасет является строго **поведенческим (behavioral)**, а не фактологическим. Цель — обучить модель структурированному формату ответа (`status`, `answer`, `citations`, `enough`), механизму цитирования конкретных номеров пассажей (`[1]`, `[2]`, `[3]`) и детерминированному возврату `NOT_FOUND`, когда факта нет в предоставленном контексте.
- **Объём:** 400 примеров (целевой диапазон 300–500).
  - `ANSWERED`: 291 пример (72.8%) со сменой позиции цитируемого пассажа (позиции [1], [2], [3] и мульти-пассажи);
  - `NOT_FOUND`: 109 примеров (27.3%) с отвлекающим контекстом и внедоменными вопросами;
  - Двуязычный баланс: румынский (ro) и русский (ru).
- **Изоляция hidden set:**
  - Закрытые примеры (`hidden: true`, g13–g16) строго исключены на этапе сбора данных;
  - Пассажи и запросы, связанные с hidden-набором, не использовались даже в качестве отвлекающего контекста (дистракторов);
  - Автоматическая проверка `verify_no_hidden_contamination` подтверждает **0 утечек**.
- **Формат:** Чистый сериализованный JSON в поле `output` без markdown-обёрток.

## QA TRAIN
- [x] Линтер ruff: чистый прогон `uv run ruff check scripts/qlora_train.py scripts/generate_behavioral_dataset.py`.
- [x] Форматирование ruff: `uv run ruff format --check scripts/qlora_train.py scripts/generate_behavioral_dataset.py`.
- [x] Тесты репозитория: `uv run pytest -q` проходит без ошибок (8 passed).
- [x] Безопасность данных: `data/golden/**` изолирован и не модифицировался.
- [x] Границы блока: затронуты только разрешённые пути (`scripts/qlora_train.py`, `scripts/generate_behavioral_dataset.py`, `data/train/**`, `models/qlora_adapter/**`, `docs/status/TRAIN.md`).
- [x] Замороженные файлы (`data/golden/**`, `data/fixture/**`, `app/**`, `frontend/**`, `pyproject.toml`) не изменялись.

## Отчёт
БЛОК: TRAIN · ЗАДАЧИ: TRAIN-QLORA, TRAIN-DATASET  
ВЛАДЕЛЕЦ: Паша  
ИЗМЕНЁННЫЕ ФАЙЛЫ:  
- `scripts/generate_behavioral_dataset.py`  
- `data/train/behavioral_dataset.jsonl`  
- `scripts/qlora_train.py`  
- `models/qlora_adapter/README.md`  
- `docs/status/TRAIN.md`  
ТЕСТЫ: все тесты проекта зелёные (8 passed).  
ВЫШЕЛ ЗА РАЗРЕШЁННЫЕ ПУТИ: нет.  

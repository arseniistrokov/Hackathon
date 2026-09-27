# Chișinău Municipal Assistant

Evidence-grounded двуязычный (RO/RU) ассистент по 40 официальным источникам Кишинёва. GigaHack 2026, трек Smart City.

> Модель формулирует ответ. Evidence определяет, имеет ли она право его дать.

## Старт
```
cp .env.example .env              # всё по умолчанию = L0: без сети, моделей и ключей
uv sync --frozen
uv run pytest -q
uv run uvicorn app.main:app --reload      # http://127.0.0.1:8000/docs
cd frontend && npm ci && npm run dev      # http://127.0.0.1:5173
git config core.hooksPath hooks           # один раз
```

## Собрать реальный корпус (CORPUS=real)

По умолчанию демо работает на `data/fixture/mini_corpus` (14 страниц, `CORPUS=fixture`). Чтобы
поднять полноценную RAG-память по 40 источникам Annex 1 (`data/sites.yaml`):

```
sed -i 's/^CORPUS=fixture/CORPUS=real/' .env      # или вручную в .env

# 1. Скачать сайты (сеть, ~10 мин на волну; падение одного сайта не роняет остальные)
uv run python -m app.blocks.fetch --wave 1          # затем --wave 2
# результат: data/raw/<site>/<slug>.md + .meta.json

# 2. (опционально) готовый архив из PR #14 — уже вычищенный текст части Annex 1
git checkout origin/data-train -- data/training/rag_memory

# 3. Собрать индекс: raw + rag_memory → chunker → SQLite (D1) → эмбеддинги (R1) → конфликты (S1)
uv run python scripts/index.py --source both --reset

# 4. Поднять сервер / прогнать eval поверх реального корпуса
uv run uvicorn app.main:app --reload
uv run python -m app.blocks.eval --all
```

`scripts/index.py --source raw|rag_memory|both [--wave 1|2] [--manual data/conflicts_manual.json] [--reset]`
пишет прогресс (сайтов/документов/чанков) в stdout. `--reset` стирает `DB_PATH`/`EMB_PATH` перед
пересборкой (полезно при повторных прогонах). Ручные конфликты (`S1`) — `data/conflicts_manual.json`
(формат как `data/fixture/conflicts.json`); без него на реальном корпусе просто нет конфликтов —
дизайнеры (G1) заполняют его по факту.

Индекс (`data/index/app.sqlite` + `embeddings.npy`) — в `.gitignore`, каждый собирает у себя;
время сборки — минуты для `rag_memory`, для полного `raw` (обе волны, сеть) — до ~15–20 минут.
Golden-набор (`data/fixture/golden.jsonl`) калиброван под fixture-корпус: на `CORPUS=real`
Recall@5/Citation закономерно ниже (другие document_id/чанки), а не показатель регресса.

## Голосовой ввод офлайн (STT)

Для локального распознавания речи (RO/RU) без отправки аудио во внешние сервисы используется `faster-whisper`. Основной путь ввода в веб-интерфейсе — захват аудио через MediaRecorder и транскрибация на локальном бэкенде (`POST /api/transcribe`), с автоматическим откатом на браузерный Web Speech API при отключённом STT или отсутствии поддержки.

1. Установите зависимости STT:
```bash
uv sync --extra stt
```

2. Настройте параметры в `.env`:
```bash
STT=whisper
WHISPER_MODEL=medium      # base (~145MB), small (~480MB), medium (~1.5GB), large-v3 (~3GB для мощных GPU)
WHISPER_DEVICE=auto       # auto / cpu / cuda
WHISPER_COMPUTE=int8      # int8 / float16
```

> **Примечание:** При первом запуске модель автоматически загружается из Hugging Face в локальный кэш. Все последующие транскрибации выполняются локально без подключения к внешним API.

## Куда смотреть
- `docs/CONTEXT.md` — решения проекта, единственный источник правды.
- `docs/BLOCKS.md` — карта блоков, владельцы, статус.
- `docs/team/README.md` — кто что делает и с чего начать; `docs/team/<Имя>.md` — твой файл.
- `docs/contracts/<ID>_*.md` — контракт блока, вставляется целиком в нейронку.
- `docs/WORKFLOW.md` — ветки, цикл задачи, ревью.
- `AGENTS.md` — правила для CLI-агентов.

Сейчас в репозитории только каркас C0: модели контрактов, порты блоков с `NotImplementedError`, fixture, контракты и референсы. Реализация блоков — по контрактам.


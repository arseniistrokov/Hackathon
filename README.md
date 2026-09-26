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

## Куда смотреть
- `docs/CONTEXT.md` — решения проекта, единственный источник правды.
- `docs/BLOCKS.md` — карта блоков, владельцы, статус.
- `docs/team/README.md` — кто что делает и с чего начать; `docs/team/<Имя>.md` — твой файл.
- `docs/contracts/<ID>_*.md` — контракт блока, вставляется целиком в нейронку.
- `docs/WORKFLOW.md` — ветки, цикл задачи, ревью.
- `AGENTS.md` — правила для CLI-агентов.

Сейчас в репозитории только каркас C0: модели контрактов, порты блоков с `NotImplementedError`, fixture, контракты и референсы. Реализация блоков — по контрактам.

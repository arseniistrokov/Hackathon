# Frontend — чат с тремя состояниями

Vite 6 + React 19 + TypeScript, без UI-кита. Один экран `src/features/chat/ChatScreen.tsx`.
В проде фронт собирается в `frontend/dist` и раздаётся FastAPI с `/` (см. `app/main.py`) — один процесс, никаких CORS.

## Запуск
```
cd frontend
npm install
npm run dev        # http://localhost:5173, /api проксируется на http://127.0.0.1:8000
npm run build      # tsc --noEmit && vite build → dist/
```

## Mock ↔ реальный API
`VITE_USE_MOCK=true` (по умолчанию) — ответы берутся из `data/fixture/mock_responses/*.json`, бэкенд не нужен.
`VITE_USE_MOCK=false` (в `.env`) — реальный `POST /api/ask`, `/api/feedback`, `/api/stats`.
Единственное место, где фронт знает про mock и про API — `src/api/client.ts`.

Правило выбора мока (только для демонстрации UI): «парков/parcare» → NOT_FOUND, «audien/приём» → CONFLICT,
«troleibuz/троллейбус» → ANSWERED с предупреждением, кириллица → RU-ответ по RO-документу, иначе RO-ответ.

## Контракт
Форма ответа — `app/contracts/models.py` (`AskResponse`, `Citation`, `Conflict`, `Meta`, …).
TS-зеркало — `src/api/types.ts`. Свои типы не заводить; не хватает поля — к Арсению.
Моки в `data/fixture/mock_responses/` — валидные `AskResponse`, их же использует бэкенд в тестах.

## Правила
- Цвета только через токены `src/styles/tokens.css` (`var(--…)`). В `src/features/**` нет `#hex` и `rgb(` — CI проверяет grep-ом.
- Все строки интерфейса — в `src/i18n.ts` (ro / ru).
- Ширина 390 px обязана работать: без горизонтального скролла, кнопки ≥ 48 px.
- Три состояния ответа (`ANSWERED` / `NOT_FOUND` / `CONFLICT`) плюс загрузка и ошибка — у каждого экрана всегда.

## Блоки
- **U1** — экран чата, карточка цитаты, блок CONFLICT в две колонки, блок NOT_FOUND с размером корпуса.
- **U2** — `FeedbackBar.tsx` (👍👎 + комментарий), `MicButton.tsx` (Web Speech API ro-RO / ru-RU), футер со статистикой.

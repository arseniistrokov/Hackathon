# Образец frontend-фичи

Раскладка (имя `chat` заменяется на `name` блока из контракта):
```
frontend/src/api/types.ts                   типы = app/contracts/models.py (snake_case). Свои поля не выдумывать
frontend/src/api/client.ts                  ask / sendFeedback / getStats; VITE_USE_MOCK=true → data/fixture/mock_responses
frontend/src/features/chat/ChatScreen.tsx   экран; только CSS-переменные из styles/tokens.css, без #hex
frontend/src/features/chat/AnswerCard.tsx   switch по response.status: ANSWERED | NOT_FOUND | CONFLICT
frontend/src/features/chat/chat.css         стили фичи через var(--token)
frontend/src/i18n.ts                        все строки интерфейса, ключ = language ответа
```
- Каркас уже рисует минимум для всех трёх состояний. Довести до макета дизайнеров, не переписывать с нуля.
- Опциональные поля (`section`, `page`, `date`, `warning`, `navigation`, `conflict`) рисуются условно: `{c.section && <span>…</span>}`.
- Состояния `loading` и `error` — обязательны у любого запроса. Ошибка сети → текст + кнопка «повторить», не белый экран.
- Проверка ширины: 390 px без горизонтального скролла, кнопки ≥ 44 px; на 1440 px `max-width` контейнера.
- `npm run typecheck && npm run build` — перед каждым коммитом.

# Референсы U2 · Пальцы, микрофон, футер статистики

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/frontend_feature/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```
frontend/src/features/feedback/FeedbackBar.tsx   👍 👎 → sendFeedback({query_id: meta.query_id, rating, comment}); после отправки — «спасибо», повторно нельзя
frontend/src/features/voice/MicButton.tsx        webkitSpeechRecognition, lang по переключателю (ro-RO / ru-RU); нет API в браузере → кнопка скрыта
frontend/src/features/stats/StatsFooter.tsx      corpus_documents, sites, conflicts, model, feedback_up/down
```

Переключатель уровня: `VITE_USE_MOCK`. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `frontend/src/features/feedback/**` — фича: каркас уже рисует минимум, довести до контракта
- `frontend/src/features/voice/**` — фича: каркас уже рисует минимум, довести до контракта
- `frontend/src/features/stats/**` — фича: каркас уже рисует минимум, довести до контракта
- `frontend/src/features/chat/ChatScreen.tsx` — фича: каркас уже рисует минимум, довести до контракта
- `frontend/src/features/chat/AnswerCard.tsx` — фича: каркас уже рисует минимум, довести до контракта

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. Клик 👍 отправляет `{query_id, rating: 1, comment}` с `query_id` из `meta` ответа; повторный клик заблокирован.
2. Микрофон: в браузере без `SpeechRecognition` кнопка не рендерится; с ним — результат распознавания попадает в поле ввода и не отправляется автоматически.
3. Футер показывает данные `/api/stats` (mock и real) и не ломает 390 px.
4. `npm run typecheck && npm run build` чисто; токены.

# Референсы U1 · Экран чата: три состояния ответа

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/frontend_feature/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```
frontend/src/api/types.ts        типы = app/contracts/models.py (snake_case, та же опциональность); свои поля не выдумывать
frontend/src/api/client.ts       ask(question, lang?) / sendFeedback / getStats; VITE_USE_MOCK=true → data/fixture/mock_responses
frontend/src/features/chat/ChatScreen.tsx   ввод + переключатель ro/ru + история; AnswerCard.tsx — switch по status; CitationCard.tsx
```
Состояния: `loading` (скелет), `error` (текст + «повторить»), `ANSWERED` (ответ, warning-баннер если есть, список CitationCard, navigation-ссылка), `NOT_FOUND` (блок с `meta.corpus_documents` и текстом «подтверждающих passages: 0, генерация заблокирована»), `CONFLICT` (две колонки a/b: value, date, passage, ссылка; ответ-пояснение сверху). Все строки — из `i18n.ts` по `language` ответа.

Переключатель уровня: `VITE_USE_MOCK=true|false`. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `frontend/src/features/chat/**` — фича: каркас уже рисует минимум, довести до контракта

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. Каждый из 5 моков `data/fixture/mock_responses/*.json` рендерится без ошибок в консоли; `undefined` в `section`, `page`, `date`, `warning`, `navigation`, `conflict` не роняет экран.
2. CONFLICT: две колонки на ≥ 768 px, одна под другой на 390 px; обе цитаты кликабельны.
3. NOT_FOUND показывает число документов корпуса и явный текст о заблокированной генерации на языке вопроса.
4. Passage в CitationCard показан дословно (не обрезан многоточием без «развернуть»), ссылка «открыть документ» ведёт на `citation.url` в новой вкладке.
5. `npm run typecheck && npm run build` чисто; в `features/**` нет `#hex`/`rgb(`.
6. Переключатель языка меняет `lang` в запросе и язык интерфейса; язык ответа берётся из `response.language`.

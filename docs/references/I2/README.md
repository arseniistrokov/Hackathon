# Референсы I2 · Нарезка страниц на chunks

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
def chunk(page: RawPage, target: int = 600, overlap: int = 90) -> list[Chunk]
def chunk_id(url: str, section: str | None, ordinal: int) -> str     # sha1(f"{url}|{section or ''}|{ordinal}")[:16]
def document_id(url: str) -> str                                      # sha1(url)[:16]
```
Правила: заголовок `## X` → `section="X"` у всех chunks под ним до следующего заголовка; `# Title` в текст chunk не входит, но `title` в модели заполнен. Абзац длиннее `target` режется по предложениям (`. `, `! `, `? `, `\n`), с overlap по символам. Абзацы короче 40 символов клеятся к следующему. Для `kind == "pdf"` маркер страницы `[[page N]]` в тексте (его ставит I1) → `page=N`, маркер из текста удаляется; заголовки статей `Articolul N`, `Art. N`, `Capitolul N` → `section`. `content_hash = sha1(text)[:16]`. Пробелы схлопываются, диакритика НЕ нормализуется (текст цитаты должен остаться дословным).

Переключатель уровня: —. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/blocks/chunker/__init__.py` — порт с `NotImplementedError`: тела заменить, сигнатуры оставить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. Каждая страница fixture даёт ≥ `expect.min_chunks_per_page` chunks; у каждого `len(text) ≤ target + overlap + 200` и `≥ 40`.
2. Страница «Regulament … petițiilor» (`expect.petition_term_url`): chunk с `expect.petition_term_passage` имеет `section` со словом `Articolul 14` и `page` не `None`.
3. Два вызова `chunk(page)` → идентичные списки (id, text, порядок).
4. `chunk_id` для одной и той же (url, section, ordinal) одинаков между вызовами и разный при разных ordinal.
5. Текст chunk содержит `ș`, `ț`, `ă` ровно как в исходнике (диакритика не потеряна и не нормализована).
6. Страница без заголовков вообще → chunks с `section=None`, не падает; пустой текст → `[]`.
7. Объединение `text` всех chunks (без overlap) покрывает ≥ 95% символов исходного текста страницы.

# Референсы I1 · Скачивание 40 сайтов

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
def load_raw(root: Path) -> list[RawPage]                 # <root>/<site>/<slug>.md + <slug>.meta.json; сортировка по (site, url)
def save_raw(page: RawPage, root: Path) -> Path           # идемпотентно; slug = безопасный из пути URL, ≤ 80 символов
def list_urls(site: str, limit: int = 150) -> list[str]   # L1: sitemap.xml → WP REST → BFS same-domain глубина 2; фильтр URL
def fetch_page(url: str, site: str) -> RawPage | None     # L1: WP REST json (content.rendered, date, modified, link) | trafilatura(html, include_links=False, output='markdown', with_metadata) | pymupdf для PDF; < 200 символов текста → None
```
CLI: `uv run python -m app.blocks.fetch --site rtec.md --limit 150` и `--wave 1` (из `data/sites.yaml`): пишет в `data/raw/`. Печатает: сайт, найдено URL, скачано, пропущено, ошибок.
Формат `.md`: первая строка `# {title}`, дальше markdown от trafilatura; для PDF — текст страниц с маркерами `[[page N]]` перед каждой страницей. `.meta.json` — все поля RawPage кроме `text`, даты ISO.
Фильтр URL (выкидывать): `/tag/`, `/category/`, `/author/`, `/page/N`, `/feed`, `?replytocom`, `/wp-json/` (кроме нашего вызова), `/wp-admin/`, `#`, новости старше 2023 (по дате из WP REST, если есть), картинки/архивы по расширению. Оставлять: услуги, контакты, регламенты, решения, тарифы, расписания, PDF.
Сеть: `httpx.Client(timeout=10, follow_redirects=True, headers={'User-Agent': 'ChisinauAssistant/0.1 (hackathon)'})`, 1 повтор, пауза 0.3 с между запросами одного сайта. `unstable: true` в sites.yaml → ошибки не считаются провалом.

Переключатель уровня: — (сеть только из CLI; тесты сети не трогают). По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/blocks/fetch/__init__.py` — порт с `NotImplementedError`: тела заменить, сигнатуры оставить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `load_raw(FIXTURE_DIR / 'mini_corpus')` возвращает `expect.documents` страниц, из них `expect.ru_documents` с `lang == 'ru'` и `expect.pdf_documents` с `kind == 'pdf'`; порядок стабилен.
2. `save_raw` → `load_raw` round-trip во временной папке даёт равные `RawPage` (включая `date=None` и диакритику в тексте); повторный `save_raw` не создаёт второй файл.
3. Фильтр URL (функция `is_wanted(url) -> bool`): `/tag/x`, `/page/2`, `?replytocom=1`, `.jpg` → False; `/servicii/`, `/contacte`, `.pdf` → True.
4. `fetch_page` при `httpx` замоканном на ошибку/таймаут → `None`, без исключения, в логе warning.
5. `fetch_page` на заранее сохранённом HTML (monkeypatch ответа) с навигацией и футером → `text` без пунктов меню, `title` из `<title>`/h1, `date` из метаданных, если есть.
6. Разбор WP REST ответа (фикстура JSON в тестах блока) → `RawPage` с `date` из `date`, `url` из `link`, `text` без HTML-тегов.

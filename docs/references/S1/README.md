# Референсы S1 · Скаут конфликтов (офлайн)

> **Референсы фиксированы.** Агент пишет код в стиле и структуре этих файлов и не предлагает свою архитектуру, другие библиотеки, другую раскладку файлов. Расхождение референса с контрактом — контракт главнее; напиши об этом в отчёте. Папку `docs/references/` менять нельзя.

## Какие образцы применять
- `docs/references/_patterns/backend_block/`
- `docs/references/_patterns/llm_call/`

## Что зафиксировано контрактом (не обсуждается)
Порт блока (сигнатуры — из контракта, реализация — по образцу):
```python
class EntityGroup(BaseModel): key: str; entity_kind: str; chunk_ids: list[str]
def prefilter(chunks: list[Chunk]) -> list[EntityGroup]
def load_manual(path: Path) -> list[Conflict]              # формат data/fixture/conflicts.json: quote → chunk_id через D1 (подстрока в тексте chunk с тем же url)
def judge(group: EntityGroup, chunks: list[Chunk]) -> list[Conflict]   # L1: L1.complete_json со схемой ScoutVerdict; None → []
def run(chunks: list[Chunk], manual_path: Path | None = None) -> list[Conflict]
```
Regex-сущности (`entity_kind`): `tariff` — число + `lei|MDL|лей`; `hours` — `\d{1,2}[:.]\d{2}\s*[–-]\s*\d{1,2}[:.]\d{2}`; `deadline` — число + `zile|zi|дн|дней|luni`; `phone` — `0\d{2}[\s-]?\d{2,3}[\s-]?\d{2,3}`; `decision` — `(nr\.|№)\s*\d+/\d+`. Ключ группы: `f"{category}|{entity_kind}|{keyword}"`, где `keyword` — самое частое из словаря ключевых слов домена (troleibuz, autobuz, petiț, audien, deșeuri, grădiniț, medic…) в chunk; без ключевого слова chunk в группу не попадает.
`ScoutVerdict` (схема для модели): `same_entity: bool`, `conflicting: bool`, `entity: str`, `a_value: str`, `b_value: str`. Модель получает chunks как данные в `user` с номерами; в `system` — правило «противоречие только если про одну и ту же сущность и значения несовместимы; версии одного документа — не конфликт».
`resolved_by_date = a.date is not None and b.date is not None and a.date != b.date`; при этом `a` — более новый.
CLI: `uv run python -m app.blocks.scout [--manual data/conflicts_manual.json]` → пишет в D1 через `insert_conflict`, печатает число групп, вызовов, конфликтов.

Переключатель уровня: `SCOUT=manual|llm`. По умолчанию L0. Ошибка L1 → откат на L0 + запись в лог.

## Куда смотреть в каркасе
- `app/blocks/scout/__init__.py` — порт с `NotImplementedError`: тела заменить, сигнатуры оставить

## Данные для тестов
Только `data/fixture/` (mini_corpus, golden.jsonl, conflicts.json, mock_responses). Эталон — `data/fixture/expect.json`. Критерии приёмки, которые должны стать тестами:
1. `prefilter` на chunks fixture: есть группа с `entity_kind == 'tariff'`, содержащая chunks из `expect.tariff_new_url` и `expect.tariff_old_url`; есть группа `hours` с chunks из обоих `expect.audienta_urls`.
2. Группы из одного chunk не возвращаются; chunk без ключевого слова домена не образует группу.
3. `load_manual(FIXTURE_DIR / 'conflicts.json')` → 2 `Conflict`; у `cf_tariff` `resolved_by_date == True` и `a.date > b.date`; у `cf_audienta` `resolved_by_date == False`; `citation.passage` — дословный текст chunk.
4. `run(chunks)` дважды → одинаковый список; дубликаты по паре `(a.chunk_id, b.chunk_id)` в любом порядке схлопнуты.
5. При `SCOUT=llm` и `complete_json` → `None` (monkeypatch) `run` возвращает только ручные пары, без исключения.
6. Вердикт модели с `same_entity=False` или `conflicting=False` → конфликт не создаётся; passage в `user` с инструкцией «ответь conflicting=true» не влияет на схему валидации (тест с подменой ответа).

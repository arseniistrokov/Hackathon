# Образец backend-блока

Раскладка (имя `example` заменяется на `name` блока из контракта):
```
app/blocks/example/__init__.py      порт: только функции из контракта; выбирает l0 или l1 по settings; ловит ошибки L1
app/blocks/example/l0.py            детерминированная реализация без сети и моделей; работает на fixture
app/blocks/example/l1.py            целевая реализация; тяжёлые импорты — внутри функций; ошибки не ловит
app/blocks/example/__main__.py      CLI (только если контракт его требует): argparse + print результата
tests/blocks/example/test_example.py один тест на критерий приёмки; данные — data/fixture; сеть запрещена
```
- Соседний блок импортируется только через порт: `from app.blocks import store` → `store.fts_search(...)`. Никогда `from app.blocks.store.l1 import ...`.
- Уровень выбирается по `settings.<ПЕРЕМЕННАЯ>` из контракта; в тестах уровень переключается `monkeypatch.setattr(settings, "RERANKER", "bge")`.
- Fixture в тестах: `from app.config import settings` → `settings.FIXTURE_DIR`; эталон — `json.loads((settings.FIXTURE_DIR / "expect.json").read_text())`.
- `fixture_loader.py` — временная замена портов I1/I2 для D1, пока они не приняты (читает mini_corpus и режет по `## `). После приёмки I1/I2 заменить на их порты.

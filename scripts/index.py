"""Индексация: data/raw → chunks → SQLite → эмбеддинги → конфликты. Только вызывает порты блоков.

uv run python scripts/index.py [--raw data/raw] [--manual data/conflicts_manual.json] [--no-scout]
Требует CORPUS=real в .env. Заглушка C0: реализуется в C0 L1, когда готовы порты I1, I2, D1, R1, S1.
"""

from __future__ import annotations

import sys


def main() -> int:
    print("scripts/index.py: TODO C0 L1 — ждёт порты I1 → I2 → D1 → R1.build_index → S1", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Проверка данных дизайнеров (блок G1): golden set, ручные конфликты, sites.yaml.

uv run python scripts/validate_data.py [--online]   (--online: каждый expected_url должен отвечать 200)
Заглушка C0: реализуется в C0 L1 до начала G1 L0.
Пока структура golden проверяется tests/test_fixture_valid.py.
"""

from __future__ import annotations

import sys


def main() -> int:
    print("scripts/validate_data.py: TODO C0 L1 — пока: uv run pytest tests/test_fixture_valid.py -q",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

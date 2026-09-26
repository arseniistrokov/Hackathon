"""uv run python -m app.blocks.eval — CLI блока E1. Гнездо создано C0."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.blocks.eval import evaluate, format_table, load_golden
from app.config import settings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", type=Path, default=settings.FIXTURE_DIR / "golden.jsonl")
    ap.add_argument("--hidden", action="store_true", help="только hidden-набор")
    ap.add_argument("--judge", action="store_true", help="LLM-судья для answer_correct (нужен LLM≠off)")
    args = ap.parse_args()
    items = load_golden(args.golden, hidden=True if args.hidden else None)
    result = evaluate(items, judge=args.judge)
    print(format_table(result))
    return 0 if not result.failures else 1


if __name__ == "__main__":
    sys.exit(main())

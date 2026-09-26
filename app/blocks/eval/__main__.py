from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.blocks.eval import evaluate, format_table, load_golden

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GOLDEN = ROOT / "data/fixture/golden.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Chișinău Municipal Assistant - E1 Eval Runner")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN, help="Path to golden.jsonl")
    parser.add_argument(
        "--hidden", action="store_true", help="Evaluate hidden items only (default: open items only)"
    )
    parser.add_argument("--all", action="store_true", help="Evaluate all items (both open and hidden)")
    parser.add_argument("--judge", action="store_true", help="Enable LLM judge for answer correctness")

    args = parser.parse_args()

    if not args.golden.exists():
        print(f"Error: Golden file not found at {args.golden}", file=sys.stderr)
        sys.exit(1)

    hidden_filter: bool | None = False
    if args.all:
        hidden_filter = None
    elif args.hidden:
        hidden_filter = True

    items = load_golden(args.golden, hidden=hidden_filter)
    result = evaluate(items, judge=args.judge)
    print(format_table(result))


if __name__ == "__main__":
    main()

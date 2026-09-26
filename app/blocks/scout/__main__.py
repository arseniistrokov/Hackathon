"""Запуск офлайн-скаута конфликтов после индексации корпуса."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from app.blocks import scout, store
from app.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Find and store conflicts between corpus chunks.")
    parser.add_argument("--manual", type=Path, default=None, help="JSON with manually curated conflict pairs")
    args = parser.parse_args()

    conn = store.connect()
    chunks = store.get_chunks(conn, store.all_chunk_ids(conn))
    groups = scout.prefilter(chunks)
    calls = 0
    if settings.SCOUT == "llm":
        from app.blocks import llm

        complete_json = llm.complete_json

        def counted_complete_json(*args: object, **kwargs: object) -> object:
            nonlocal calls
            calls += 1
            return complete_json(*args, **kwargs)

        with patch.object(llm, "complete_json", counted_complete_json):
            conflicts = scout.run(chunks, manual_path=args.manual)
    else:
        conflicts = scout.run(chunks, manual_path=args.manual)
    for conflict in conflicts:
        store.insert_conflict(conn, conflict)
    print(f"groups={len(groups)} calls={calls} conflicts={len(conflicts)}")


if __name__ == "__main__":
    main()

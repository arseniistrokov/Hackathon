"""Детерминированные операции S1 без вызова модели."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from app.blocks import store
from app.blocks.scout import EntityGroup
from app.contracts.models import Chunk, Citation, Conflict, ConflictSide

_ENTITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "tariff": re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:lei|MDL|лей)\b", re.IGNORECASE),
    "hours": re.compile(r"\d{1,2}[:.]\d{2}\s*[–-]\s*\d{1,2}[:.]\d{2}"),
    "deadline": re.compile(r"\b\d+\s*(?:zile|zi|дн\w*|дней|luni)\b", re.IGNORECASE),
    "phone": re.compile(r"0\d{2}[\s-]?\d{2,3}[\s-]?\d{2,3}"),
    "decision": re.compile(r"(?:nr\.|№)\s*\d+/\d+", re.IGNORECASE),
}
_KEYWORDS = (
    "troleibuz",
    "autobuz",
    "petiț",
    "audien",
    "deșeuri",
    "grădiniț",
    "medic",
    "contact",
    "transport",
    "salubriz",
    "program",
    "taxă",
    "tarif",
    "telefon",
)


def _fold_keyword_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def prefilter(chunks: list[Chunk]) -> list[EntityGroup]:
    grouped: dict[tuple[str, str], dict[str, Chunk]] = defaultdict(dict)

    for chunk in chunks:
        folded_text = _fold_keyword_text(chunk.text)
        keyword_counts = Counter(
            {
                keyword: len(re.findall(re.escape(_fold_keyword_text(keyword)), folded_text))
                for keyword in _KEYWORDS
            }
        )
        matched_keywords = [keyword for keyword, count in keyword_counts.items() if count]
        if not matched_keywords:
            continue
        keyword = min(matched_keywords, key=lambda item: (-keyword_counts[item], _KEYWORDS.index(item)))

        for entity_kind, pattern in _ENTITY_PATTERNS.items():
            if not pattern.search(chunk.text):
                continue
            key = (entity_kind, keyword)
            grouped[key].setdefault(chunk.id, chunk)

    result: list[EntityGroup] = []
    for (entity_kind, keyword), chunk_by_id in sorted(grouped.items()):
        matching_chunks = list(chunk_by_id.values())
        if len(matching_chunks) < 2:
            continue
        category_counts = Counter(chunk.category for chunk in matching_chunks)
        category = min(category_counts, key=lambda item: (-category_counts[item], item))
        result.append(
            EntityGroup(
                key=f"{category}|{entity_kind}|{keyword}",
                entity_kind=entity_kind,
                chunk_ids=sorted(chunk.id for chunk in matching_chunks),
            )
        )
    return result


def load_manual(path: Path) -> list[Conflict]:
    raw_conflicts = json.loads(path.read_text(encoding="utf-8"))
    conn = store.connect()
    chunks = store.get_chunks(conn, store.all_chunk_ids(conn))
    by_url: dict[str, list[Chunk]] = defaultdict(list)
    for chunk in chunks:
        by_url[chunk.url].append(chunk)

    conflicts: list[Conflict] = []
    for raw in raw_conflicts:
        sides = [_manual_side(raw[side], by_url) for side in ("a", "b")]
        a, b = sides
        resolved_by_date = a.date is not None and b.date is not None and a.date != b.date
        if resolved_by_date and a.date < b.date:
            a, b = b, a
        conflicts.append(
            Conflict(
                id=raw["id"],
                entity=raw["entity"],
                a=a,
                b=b,
                resolved_by_date=resolved_by_date,
            )
        )
    return sorted(conflicts, key=lambda conflict: conflict.id)


def deduplicate(conflicts: list[Conflict]) -> list[Conflict]:
    unique: dict[tuple[str, str], Conflict] = {}
    for conflict in conflicts:
        pair = tuple(sorted((conflict.a.citation.chunk_id, conflict.b.citation.chunk_id)))
        unique.setdefault(pair, conflict)
    return [unique[pair] for pair in sorted(unique)]


def _manual_side(raw: dict[str, str | None], by_url: dict[str, list[Chunk]]) -> ConflictSide:
    quote = raw["quote"]
    chunk = next(
        (
            candidate
            for candidate in by_url.get(raw["url"], [])
            if quote.casefold() in candidate.text.casefold()
        ),
        None,
    )
    if chunk is None:
        raise ValueError(f"Manual conflict quote not found in D1 for URL: {raw['url']}")

    value_date = date.fromisoformat(raw["date"]) if raw.get("date") else chunk.date
    citation = Citation(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        title=chunk.title,
        url=chunk.url,
        site=chunk.site,
        section=chunk.section,
        page=chunk.page,
        passage=chunk.text,
        date=chunk.date,
    )
    return ConflictSide(citation=citation, value=raw["value"], date=value_date)

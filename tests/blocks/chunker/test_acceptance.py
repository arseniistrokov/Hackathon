from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from app.blocks.chunker import chunk, chunk_id, document_id
from app.contracts.models import RawPage
from docs.references._patterns.backend_block.fixture_loader import load_raw

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "data" / "fixture"
EXPECT = json.loads((FIXTURE / "expect.json").read_text(encoding="utf-8"))
PAGES = load_raw(FIXTURE / "mini_corpus")


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.url)
def test_fixture_pages_produce_chunks_within_size_bounds(page: RawPage) -> None:
    chunks = chunk(page)

    assert len(chunks) >= EXPECT["min_chunks_per_page"]
    assert all(40 <= len(item.text) <= 600 + 90 + 200 for item in chunks)


def test_pdf_petition_passage_keeps_article_and_page_metadata() -> None:
    page = next(page for page in PAGES if page.url == EXPECT["petition_term_url"])

    matching = [item for item in chunk(page) if EXPECT["petition_term_passage"] in item.text]

    assert matching
    assert any("Articolul 14" in (item.section or "") and item.page is not None for item in matching)


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.url)
def test_chunking_is_deterministic(page: RawPage) -> None:
    first = chunk(page)
    second = chunk(page)

    assert [(item.id, item.text, item.section, item.page) for item in first] == [
        (item.id, item.text, item.section, item.page) for item in second
    ]


def test_hash_ids_are_deterministic_and_ordinal_sensitive() -> None:
    url = PAGES[0].url

    expected_chunk_id = hashlib.sha1(f"{url}|Articolul 14|0".encode()).hexdigest()[:16]
    assert chunk_id(url, "Articolul 14", 0) == expected_chunk_id
    assert chunk_id(url, "Articolul 14", 0) != chunk_id(url, "Articolul 14", 1)
    assert document_id(url) == hashlib.sha1(url.encode()).hexdigest()[:16]


def test_chunk_text_preserves_romanian_diacritics() -> None:
    page = next(page for page in PAGES if "ș" in page.text and "ț" in page.text and "ă" in page.text)

    text = " ".join(item.text for item in chunk(page))

    assert all(mark in text for mark in ("ș", "ț", "ă"))


def test_headerless_and_empty_fixture_derived_pages_are_supported() -> None:
    source = next(page for page in PAGES if len(page.text) >= 100)
    headerless = source.model_copy(update={"text": source.text.replace("#", "")})
    empty = source.model_copy(update={"text": ""})

    assert chunk(empty) == []
    assert chunk(headerless)
    assert all(item.section is None for item in chunk(headerless))


def test_chunks_cover_at_least_95_percent_of_fixture_text() -> None:
    page = max(PAGES, key=lambda candidate: len(candidate.text))
    chunks = chunk(page)
    source = " ".join(
        line.strip()
        for line in page.text.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and not line.strip().startswith("[[page ")
    )
    rebuilt = chunks[0].text if chunks else ""
    for previous, current in zip(chunks, chunks[1:], strict=False):
        max_overlap = min(90, len(previous.text), len(current.text))
        overlap_size = next(
            (size for size in range(max_overlap, 19, -1) if previous.text[-size:] == current.text[:size]),
            0,
        )
        rebuilt += " " + current.text[overlap_size:]
    source_words = source.split()
    rebuilt_words = rebuilt.split()
    position = 0
    covered = 0
    for word in source_words:
        try:
            position = rebuilt_words.index(word, position) + 1
            covered += len(word) + 1
        except ValueError:
            continue

    assert covered / len(source) >= 0.95


def test_long_fixture_paragraphs_split_with_overlap_without_losing_words() -> None:
    page = max(PAGES, key=lambda candidate: len(candidate.text))
    chunks = chunk(page, target=120, overlap=20)

    assert all(40 <= len(item.text) <= 120 for item in chunks)
    source = " ".join(
        line.strip()
        for line in page.text.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and not line.strip().startswith("[[page ")
    )
    output = " ".join(item.text for item in chunks)
    source_words = source.split()
    output_words = output.split()
    position = 0
    for word in source_words:
        position = output_words.index(word, position) + 1

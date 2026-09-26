from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.blocks.fetch import fetch_page, list_urls, load_raw, save_raw
from app.config import settings
from app.contracts.models import RawPage
from docs.references._patterns.backend_block.fixture_loader import load_raw as load_fixture

FIXTURE_ROOT = settings.FIXTURE_DIR / "mini_corpus"
EXPECT = json.loads((settings.FIXTURE_DIR / "expect.json").read_text(encoding="utf-8"))
FIXTURE_PAGES = load_fixture(FIXTURE_ROOT)


def test_load_raw_matches_fixture_counts_and_stable_order() -> None:
    first = load_raw(FIXTURE_ROOT)
    second = load_raw(FIXTURE_ROOT)

    assert len(first) == EXPECT["documents"]
    assert sum(page.lang == "ru" for page in first) == EXPECT["ru_documents"]
    assert sum(page.kind == "pdf" for page in first) == EXPECT["pdf_documents"]
    assert [(page.site, page.url) for page in first] == sorted((page.site, page.url) for page in first)
    assert first == second


@pytest.mark.parametrize("page", FIXTURE_PAGES, ids=lambda page: page.url)
def test_save_raw_round_trips_fixture_page_and_is_idempotent(page: RawPage, tmp_path: Path) -> None:
    saved_path = save_raw(page, tmp_path)
    saved_again = save_raw(page, tmp_path)

    assert saved_path == saved_again
    assert load_raw(tmp_path) == [page]
    assert len(list(tmp_path.rglob("*.meta.json"))) == 1
    assert len(saved_path.stem) <= 80
    assert saved_path.read_text(encoding="utf-8").splitlines()[0] == f"# {page.title}"


def test_l1_ports_are_disabled_in_l0() -> None:
    with pytest.raises(RuntimeError, match="L1"):
        list_urls("rtec.md")
    with pytest.raises(RuntimeError, match="L1"):
        fetch_page("https://rtec.md/", "rtec.md")

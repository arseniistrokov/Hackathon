"""Fixture валиден и согласован с моделями контрактов и data/sites.yaml. Без сети.

Запуск: uv run pytest tests/test_fixture_valid.py -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from app.contracts.models import AskResponse, GoldenItem, RawPage

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixture"
CORPUS = FIXTURE / "mini_corpus"


@pytest.fixture(scope="module")
def expect() -> dict:
    return json.loads((FIXTURE / "expect.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sites() -> dict:
    return yaml.safe_load((ROOT / "data" / "sites.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pages() -> list[RawPage]:
    out: list[RawPage] = []
    for meta_path in sorted(CORPUS.rglob("*.meta.json")):
        md_path = meta_path.with_name(meta_path.name.replace(".meta.json", ".md"))
        assert md_path.is_file(), f"нет .md для {meta_path}"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        expected_keys = {"site", "url", "title", "category", "lang", "date", "kind", "fetched_at"}
        assert set(meta) == expected_keys, meta_path
        assert meta_path.parent.name == meta["site"], f"папка ≠ site в {meta_path}"
        out.append(RawPage(text=md_path.read_text(encoding="utf-8"), **meta))
    return out


@pytest.fixture(scope="module")
def golden() -> list[GoldenItem]:
    lines = (FIXTURE / "golden.jsonl").read_text(encoding="utf-8").splitlines()
    return [GoldenItem(**json.loads(line)) for line in lines if line.strip()]


def test_pages_counts(pages: list[RawPage], expect: dict) -> None:
    assert len(pages) == expect["documents"]
    assert len({p.site for p in pages}) == expect["sites"]
    assert sum(p.lang == "ru" for p in pages) == expect["ru_documents"]
    assert sum(p.kind == "pdf" for p in pages) == expect["pdf_documents"]
    assert len({p.url for p in pages}) == len(pages), "url дублируются"


def test_pages_have_sections_for_chunking(pages: list[RawPage], expect: dict) -> None:
    for p in pages:
        assert p.text.startswith("# "), p.url
        assert p.text.count("\n## ") >= expect["min_chunks_per_page"], p.url
        assert 900 <= len(p.text) <= 2500, (p.url, len(p.text))


def test_pages_match_sites_yaml(pages: list[RawPage], sites: dict) -> None:
    for p in pages:
        assert p.site in sites, p.site
        assert p.category == sites[p.site]["category"], p.url


def test_not_found_guard(pages: list[RawPage]) -> None:
    for p in pages:
        low = p.text.lower()
        for bad in ("parcare", "parcăr", "парков", "собак", "câin"):
            assert bad not in low, (p.url, bad)


def test_golden_valid(golden: list[GoldenItem], pages: list[RawPage], expect: dict) -> None:
    assert len(golden) == expect["golden_total"]
    assert sum(g.hidden for g in golden) == expect["golden_hidden"]
    assert len({g.id for g in golden}) == len(golden)
    by_status: dict[str, int] = {}
    for g in golden:
        by_status[g.expected_status] = by_status.get(g.expected_status, 0) + 1
    assert by_status == expect["golden_by_status"]
    categories = {g.category for g in golden}
    assert len(categories) == 8, categories
    by_url = {p.url: p for p in pages}
    for g in golden:
        if g.expected_status == "NOT_FOUND":
            assert g.expected_url is None and g.expected_passage is None, g.id
            continue
        assert g.expected_url in by_url, g.id
        assert g.expected_passage and len(g.expected_passage) <= 120, g.id
        assert g.expected_passage in by_url[g.expected_url].text, g.id


def test_expect_urls_exist(expect: dict, pages: list[RawPage], golden: list[GoldenItem]) -> None:
    urls = {p.url for p in pages}
    for key in ("petition_term_url", "tariff_new_url", "tariff_old_url"):
        assert expect[key] in urls, key
    assert set(expect["audienta_urls"]) <= urls
    by_url = {p.url: p for p in pages}
    assert expect["petition_term_passage"] in by_url[expect["petition_term_url"]].text
    queries = {g.query for g in golden if g.expected_status == "NOT_FOUND"}
    assert set(expect["not_found_queries"]) == queries
    assert expect["navigation"]["autosalubritate.md"]["url"] in urls


def test_conflicts_shape(pages: list[RawPage]) -> None:
    conflicts = json.loads((FIXTURE / "conflicts.json").read_text(encoding="utf-8"))
    assert len(conflicts) == 2
    by_url = {p.url: p for p in pages}
    for c in conflicts:
        assert set(c) == {"id", "entity", "entity_kind", "a", "b", "resolved_by_date"}
        for side in (c["a"], c["b"]):
            assert set(side) == {"url", "quote", "value", "date"}
            assert side["url"] in by_url, c["id"]
            assert side["quote"] in by_url[side["url"]].text, c["id"]
        both_dated = c["a"]["date"] is not None and c["b"]["date"] is not None
        assert c["resolved_by_date"] == both_dated, c["id"]


def test_mock_responses_valid(pages: list[RawPage]) -> None:
    files = sorted((FIXTURE / "mock_responses").glob("*.json"))
    assert {f.name for f in files} == {
        "answered_ro.json", "answered_ru_from_ro_doc.json", "not_found.json", "conflict.json",
        "answered_with_warning.json",
    }
    by_url = {p.url: p for p in pages}
    statuses = set()
    for f in files:
        resp = AskResponse(**json.loads(f.read_text(encoding="utf-8")))
        statuses.add(resp.status)
        for c in resp.citations:
            assert c.url in by_url, f.name
            assert c.passage in by_url[c.url].text, f.name
        if resp.status == "NOT_FOUND":
            assert resp.answer == "" and not resp.citations
        if resp.status == "CONFLICT":
            assert resp.conflict is not None and not resp.conflict.resolved_by_date
        if f.name == "answered_with_warning.json":
            assert resp.warning
    assert statuses == {"ANSWERED", "NOT_FOUND", "CONFLICT"}

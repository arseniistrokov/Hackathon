"""Тесты блока <ID>. Один критерий приёмки = минимум один тест. Данные — только fixture, сеть запрещена.

Запуск: uv run pytest tests/blocks/example -q
"""

from __future__ import annotations

import json

import pytest

from app.blocks.rerank import is_enough, rerank
from app.config import settings
from app.contracts.models import Chunk, Passage, Query


@pytest.fixture(scope="module")
def expect() -> dict:
    return json.loads((settings.FIXTURE_DIR / "expect.json").read_text(encoding="utf-8"))


def _passage(n: int, text: str, url: str = "https://example.md/p") -> Passage:
    chunk = Chunk(id=f"c{n:015d}", document_id="d" * 16, site="rtec.md", category="mobility", url=url,
                  title="t", text=text, content_hash="h" * 16)
    return Passage(n=n, chunk=chunk, score=0.0, sources=["fts"])


def test_petition_passage_ranks_first(expect: dict) -> None:
    """Критерий 1: passage с термином петиции — первый, is_enough → True."""
    q = Query(text="Care este termenul de examinare a petiției?", lang="ro",
              search_text="Care este termenul de examinare a petiției?")
    ps = [_passage(1, "Orarul troleibuzelor se afișează la stație."), _passage(2, expect["petition_term_passage"])]
    top = rerank(q, ps)
    assert expect["petition_term_passage"] in top[0].chunk.text
    assert is_enough(top)


def test_diacritics_do_not_change_score() -> None:
    """Критерий 4: petitie и petiție дают одинаковый скор."""
    p = [_passage(1, "Petițiile se examinează în termen de 30 de zile.")]
    a = rerank(Query(text="petitie termen", lang="ro", search_text="petitie termen"), p)[0].score
    b = rerank(Query(text="petiție termen", lang="ro", search_text="petiție termen"), p)[0].score
    assert a == b


def test_l1_failure_falls_back_to_l0(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ошибка L1 не выходит наружу: порт откатывается на L0."""
    import app.blocks.rerank as port

    monkeypatch.setattr(settings, "RERANKER", "bge")
    monkeypatch.setattr(port, "l1", type("L1", (), {"rerank": staticmethod(lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))}), raising=False)
    q = Query(text="x", lang="ro", search_text="x")
    assert rerank(q, [_passage(1, "x y")]) != []

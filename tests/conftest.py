"""Общие фикстуры для всех тестов.

D1 (app/blocks/store) держит fixture-корпус в одном общем shared-cache in-memory SQLite на
процесс (иначе save_query/save_feedback/insert_conflict не видны другим connect()). Между
тестами это нужно сбрасывать, иначе один тест видит записи другого.
"""

from __future__ import annotations

import pytest
from app.blocks import store


@pytest.fixture(autouse=True)
def _reset_store_fixture_db():
    yield
    store.reset_fixture()

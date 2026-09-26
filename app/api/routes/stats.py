"""GET /api/stats — блок A1. Гнездо создано C0."""

from fastapi import APIRouter

from app.blocks import llm, store
from app.contracts.models import Stats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=Stats)
def get_stats() -> Stats:
    conn = store.connect()
    try:
        with conn:
            stats = store.stats(conn)
    finally:
        conn.close()
    return stats.model_copy(update={"model": llm.model_name()})

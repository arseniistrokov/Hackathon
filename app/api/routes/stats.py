"""GET /api/stats — блок A1. Гнездо создано C0."""

from fastapi import APIRouter

from app.contracts.models import Stats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=Stats)
def get_stats() -> Stats:
    raise NotImplementedError("A1: собрать из D1.stats() и settings")

"""GET /api/health — что за уровни включены. Каркас C0, менять не нужно."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "corpus": settings.CORPUS,
        "llm": settings.LLM,
        "embedder": settings.EMBEDDER,
        "reranker": settings.RERANKER,
        "stt": settings.STT,
    }

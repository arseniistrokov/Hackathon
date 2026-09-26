"""POST /api/feedback — блок A1. Гнездо создано C0: тело функции заменяется, сигнатура — нет."""

from fastapi import APIRouter

from app.contracts.models import FeedbackRequest

router = APIRouter(tags=["feedback"])


@router.post("/feedback", status_code=201)
def post_feedback(body: FeedbackRequest) -> dict[str, str]:
    raise NotImplementedError("A1: сохранить в D1.save_feedback и вернуть {'status': 'saved'}")

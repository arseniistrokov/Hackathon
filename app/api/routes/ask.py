"""POST /api/ask — блок A1. Роут только вызывает порт W1 и ничего не считает сам."""

from fastapi import APIRouter

from app.blocks.workflow import ask
from app.contracts.models import AskRequest, AskResponse

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def post_ask(body: AskRequest) -> AskResponse:
    return ask(body.question, body.lang)

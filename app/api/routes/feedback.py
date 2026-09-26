"""POST /api/feedback — блок A1. Гнездо создано C0: тело функции заменяется, сигнатура — нет."""

import sqlite3

from fastapi import APIRouter, HTTPException

from app.blocks import store
from app.contracts.models import FeedbackRequest

router = APIRouter(tags=["feedback"])


@router.post("/feedback", status_code=201)
def post_feedback(body: FeedbackRequest) -> dict[str, str]:
    conn = store.connect()
    try:
        with conn:
            store.save_feedback(conn, body.query_id, body.rating, body.comment)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=404, detail="Unknown query_id") from exc
    finally:
        conn.close()
    return {"status": "saved"}

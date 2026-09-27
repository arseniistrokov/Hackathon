"""Регистрация роутов. ЗАМОРОЖЕН после C0. Новый роут — к Арсению."""

from fastapi import APIRouter

from app.api.routes import ask, feedback, health, stats, transcribe

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ask.router)
api_router.include_router(feedback.router)
api_router.include_router(stats.router)
api_router.include_router(transcribe.router)


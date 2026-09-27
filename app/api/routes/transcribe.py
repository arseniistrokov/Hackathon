"""POST /api/transcribe — распознавание речи через faster-whisper."""

from __future__ import annotations

import io
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.blocks.stt import transcribe as stt_transcribe
from app.config import settings

log = logging.getLogger(__name__)

router = APIRouter(tags=["stt"])

MAX_AUDIO_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_DURATION_SECONDS = 25.0


class TranscribeResponse(BaseModel):
    text: str
    lang: str | None = None
    duration_ms: int | None = None


@router.post("/transcribe", response_model=TranscribeResponse)
async def post_transcribe(
    audio: Annotated[UploadFile, File()],
    lang: Annotated[Literal["ro", "ru"] | None, Form()] = None,
) -> TranscribeResponse:
    if settings.STT == "off":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STT service is disabled (STT=off)",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio file is empty",
        )

    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds 2 MB limit ({len(audio_bytes)} bytes)",
        )

    # Validate audio duration if container format is recognizable
    try:
        import av  # optional dependency (extra "stt"); lazy so the app boots without it

        container = av.open(io.BytesIO(audio_bytes))
        if container.duration is not None and av.time_base:
            duration_sec = float(container.duration / av.time_base)
            if duration_sec > MAX_DURATION_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio duration exceeds 25 seconds limit ({duration_sec:.1f}s)",
                )
    except HTTPException:
        raise
    except Exception:
        # Fall back gracefully for mock bytes or non-standard streams
        pass

    try:
        result = stt_transcribe(audio_bytes, lang_hint=lang)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        log.exception("STT transcription error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {e}",
        ) from e

    return TranscribeResponse(**result)

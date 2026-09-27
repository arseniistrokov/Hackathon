"""Блок STT: локальное распознавание речи через faster-whisper (singleton)."""

from __future__ import annotations

import io
import logging
import time
from typing import Any, Literal

from app.config import settings

log = logging.getLogger(__name__)

_model: Any = None


def _get_model(force_cpu: bool = False) -> Any:
    global _model
    if _model is None or force_cpu:
        from faster_whisper import WhisperModel

        device = "cpu" if force_cpu else settings.WHISPER_DEVICE
        compute_type = "int8" if force_cpu else settings.WHISPER_COMPUTE

        log.info(
            "STT: loading faster-whisper model=%s device=%s compute_type=%s",
            settings.WHISPER_MODEL,
            device,
            compute_type,
        )
        try:
            _model = WhisperModel(
                settings.WHISPER_MODEL,
                device=device,
                compute_type=compute_type,
            )
        except Exception as e:
            if device != "cpu":
                log.warning("STT: failed loading with device=%s (%s), falling back to cpu", device, e)
                _model = WhisperModel(
                    settings.WHISPER_MODEL,
                    device="cpu",
                    compute_type="int8",
                )
            else:
                raise
    return _model


def transcribe(
    audio_bytes: bytes, lang_hint: Literal["ro", "ru"] | None = None
) -> dict[str, Any]:
    """Транскрибирует аудио-байты (webm/ogg/wav) в текст.

    При settings.STT == 'off' бросает RuntimeError.
    """
    if settings.STT == "off":
        raise RuntimeError("STT is disabled (STT=off)")

    start_t = time.perf_counter()
    model = _get_model()

    audio_stream = io.BytesIO(audio_bytes)
    try:
        segments, info = model.transcribe(
            audio_stream,
            language=lang_hint,
            beam_size=1,
            vad_filter=True,
        )
        text = "".join(segment.text for segment in segments).strip()
    except RuntimeError as e:
        if "cublas" in str(e).lower() or "cuda" in str(e).lower():
            log.warning("STT: CUDA runtime failure (%s), retrying on CPU...", e)
            model = _get_model(force_cpu=True)
            audio_stream.seek(0)
            segments, info = model.transcribe(
                audio_stream,
                language=lang_hint,
                beam_size=1,
                vad_filter=True,
            )
            text = "".join(segment.text for segment in segments).strip()
        else:
            raise

    duration_ms = int((time.perf_counter() - start_t) * 1000)
    detected_lang = getattr(info, "language", lang_hint) or lang_hint

    return {
        "text": text,
        "lang": detected_lang,
        "duration_ms": duration_ms,
    }

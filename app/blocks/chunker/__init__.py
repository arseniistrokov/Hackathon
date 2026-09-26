"""Блок I2 · chunker. Чистая функция, без сети и без уровней.

Контракт: docs/contracts/I2_chunker.md. Владелец: Никита.
"""

from __future__ import annotations

import hashlib
import re

from app.contracts.models import Chunk, RawPage


def chunk(page: RawPage, target: int = 600, overlap: int = 90) -> list[Chunk]:
    """Разбить страницу по заголовкам → абзацам на chunks ~target символов с overlap. Детерминировано."""
    if not page.text.strip():
        return []
    if target < 1 or overlap < 0:
        raise ValueError("target must be positive and overlap cannot be negative")

    blocks: list[tuple[str | None, int | None, str]] = []
    section: str | None = None
    page_number: int | None = 1 if page.kind == "pdf" else None
    body: list[str] = []

    def flush() -> None:
        text = " ".join(" ".join(body).split())
        if text:
            blocks.append((section, page_number, text))
        body.clear()

    for line in page.text.splitlines():
        page_match = re.fullmatch(r"\s*\[\[page\s+(\d+)\]\]\s*", line, flags=re.IGNORECASE)
        if page_match:
            flush()
            page_number = int(page_match.group(1))
            continue

        heading = re.match(r"^\s{0,3}(#{1,3})\s+(.+?)\s*#*\s*$", line)
        article = re.match(r"^\s*((?:Articolul|Art\.|Capitolul)\s+\d+[^\n]*)\s*$", line, flags=re.IGNORECASE)
        if heading:
            flush()
            if len(heading.group(1)) == 1:
                continue
            section = heading.group(2).strip()
            continue
        if article and page.kind == "pdf":
            flush()
            section = article.group(1).strip()
            continue
        if not line.strip():
            flush()
        else:
            body.append(line.strip())
    flush()

    # Join short paragraphs forward, retaining their section and page metadata.
    merged: list[tuple[str | None, int | None, str]] = []
    for current_section, current_page, text in blocks:
        if merged and len(merged[-1][2]) < 40 and merged[-1][:2] == (current_section, current_page):
            previous = merged.pop()
            text = f"{previous[2]} {text}"
        if len(text) < 40 and merged and merged[-1][:2] == (current_section, current_page):
            previous = merged.pop()
            text = f"{previous[2]} {text}"
        merged.append((current_section, current_page, text))

    chunks: list[Chunk] = []
    ordinal = 0
    for current_section, current_page, text in merged:
        if len(text) <= target:
            pieces = [text]
        else:
            pieces = []
            start = 0
            while start < len(text):
                end = min(start + target, len(text))
                if end < len(text):
                    boundary = max(text.rfind(mark, start + 40, end) for mark in (". ", "! ", "? ", " "))
                    if boundary > start:
                        end = boundary + (2 if text[boundary : boundary + 2] in {". ", "! ", "? "} else 1)
                    if 0 < len(text) - end < 40:
                        end = len(text) - 40
                pieces.append(text[start:end].strip())
                if end == len(text):
                    break
                start = max(end - overlap, start + 1)
        for piece in pieces:
            piece = " ".join(piece.split())
            if len(piece) < 40 and chunks:
                previous = chunks[-1]
                combined = f"{previous.text} {piece}".strip()
                chunks[-1] = previous.model_copy(
                    update={
                        "text": combined,
                        "content_hash": hashlib.sha1(combined.encode()).hexdigest()[:16],
                    }
                )
                continue
            chunks.append(
                Chunk(
                    id=chunk_id(page.url, current_section, ordinal),
                    document_id=document_id(page.url),
                    site=page.site,
                    category=page.category,
                    url=page.url,
                    title=page.title,
                    section=current_section,
                    page=current_page,
                    text=piece,
                    lang=page.lang,
                    date=page.date,
                    content_hash=hashlib.sha1(piece.encode()).hexdigest()[:16],
                )
            )
            ordinal += 1
    return chunks


def chunk_id(url: str, section: str | None, ordinal: int) -> str:
    """sha1(f'{url}|{section or ""}|{ordinal}')[:16]."""
    return hashlib.sha1(f"{url}|{section or ''}|{ordinal}".encode()).hexdigest()[:16]


def document_id(url: str) -> str:
    """sha1(url)[:16]."""
    return hashlib.sha1(url.encode()).hexdigest()[:16]

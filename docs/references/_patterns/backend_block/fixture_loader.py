"""Временная замена портов I1 (load_raw) и I2 (chunk) для блока D1, пока они не приняты.

Читает data/fixture/mini_corpus/<site>/<slug>.md + .meta.json, режет по заголовкам `## `.
После приёмки I1/I2 в D1 заменить на `from app.blocks import fetch, chunker`.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from app.contracts.models import Chunk, RawPage


def load_raw(root: Path) -> list[RawPage]:
    pages: list[RawPage] = []
    for meta_path in sorted(root.glob("*/*.meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        text = meta_path.with_name(meta_path.name.replace(".meta.json", ".md")).read_text(encoding="utf-8")
        pages.append(RawPage(text=text, **meta))
    return sorted(pages, key=lambda p: (p.site, p.url))


def document_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16]


def chunk(page: RawPage) -> list[Chunk]:
    doc_id = document_id(page.url)
    out: list[Chunk] = []
    section: str | None = None
    ordinal = 0
    for block in re.split(r"\n(?=#{1,3} )", page.text):
        m = re.match(r"(#{1,3}) (.+)\n?", block)
        if m:
            if m.group(1) == "#":
                block = block[m.end():]
            else:
                section = m.group(2).strip()
                block = block[m.end():]
        body = re.sub(r"\[\[page \d+\]\]", "", block).strip()
        if len(body) < 40:
            continue
        page_no = None
        pm = re.search(r"\[\[page (\d+)\]\]", block)
        if pm:
            page_no = int(pm.group(1))
        cid = hashlib.sha1(f"{page.url}|{section or ''}|{ordinal}".encode()).hexdigest()[:16]
        out.append(Chunk(id=cid, document_id=doc_id, site=page.site, category=page.category, url=page.url,
                         title=page.title, section=section, page=page_no, text=body, lang=page.lang,
                         date=page.date, content_hash=hashlib.sha1(body.encode()).hexdigest()[:16]))
        ordinal += 1
    return out

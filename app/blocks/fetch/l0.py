"""Локальная загрузка и сохранение RawPage без сетевых обращений."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.contracts.models import RawPage


def load_raw(root: Path) -> list[RawPage]:
    pages: list[RawPage] = []
    for meta_path in sorted(root.glob("*/*.meta.json")):
        markdown_path = meta_path.with_name(meta_path.name.removesuffix(".meta.json") + ".md")
        if not markdown_path.is_file():
            continue
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        text = markdown_path.read_text(encoding="utf-8")
        pages.append(RawPage.model_validate({**metadata, "text": text}))
    return sorted(pages, key=lambda page: (page.site, page.url))


def save_raw(page: RawPage, root: Path) -> Path:
    path = urlsplit(page.url).path.rstrip("/")
    raw_slug = unquote(path.rsplit("/", maxsplit=1)[-1]) if path else "index"
    slug = re.sub(r"[^\w.-]+", "-", raw_slug, flags=re.UNICODE).strip(".-_") or "index"
    slug = slug[:80]
    if slug.upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{n}" for n in range(1, 10)),
        *(f"LPT{n}" for n in range(1, 10)),
    }:
        slug = f"_{slug}"

    site_dir = root / page.site
    site_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = site_dir / f"{slug}.md"
    metadata_path = site_dir / f"{slug}.meta.json"
    markdown_path.write_text(page.text, encoding="utf-8")
    metadata = page.model_dump(mode="json", exclude={"text"})
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return markdown_path

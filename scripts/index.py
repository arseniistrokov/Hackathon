"""Индексация: data/raw и/или data/training/rag_memory → chunker → store.upsert →
retrieval.build_index → scout. Только вызывает порты блоков I1, I2, D1, R1, S1.

uv run python scripts/index.py [--source raw|rag_memory|both] [--wave 1|2] [--manual PATH] [--reset]
Требует CORPUS=real в .env (иначе пишет предупреждение и работает поверх фикстур — для
CI/локальной проверки без сети такой запуск бессмысленен, но не падает).
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import yaml
from app.blocks import chunker, retrieval, scout, store
from app.blocks.fetch import l0 as fetch_l0
from app.blocks.scout import l0 as scout_l0
from app.config import ROOT, settings
from app.contracts.models import RawPage

log = logging.getLogger("index")

RAW_DIR = ROOT / "data" / "raw"
RAG_MEMORY_DIR = ROOT / "data" / "training" / "rag_memory"

_FRONTMATTER_RE = re.compile(r"\A(#[^\n]*\n+)?---\n.*?\n---\n+", re.DOTALL)


def _strip_frontmatter(text: str) -> str:
    """PR #14 (data-train) пишет trafilatura YAML frontmatter (title/url/hostname/...) внутри
    самого .md перед текстом. Для fetch (I1 L1) такого нет. Срезаем перед chunk(), иначе он
    попадает первым чанком документа и портит цитаты/rerank."""
    return _FRONTMATTER_RE.sub("", text, count=1)


def _load_pages(source: str, wave: int | None) -> list[RawPage]:
    """Собрать RawPage из data/raw и/или data/training/rag_memory, убрать дубликаты по url.

    raw (свежая загрузка I1) имеет приоритет над rag_memory (архив PR #14), т.к. может быть
    полнее/новее. wave фильтрует по data/sites.yaml (wave 1/2), если задан.
    """
    sites: dict = {}
    if wave is not None:
        sites = yaml.safe_load(settings.SITES_PATH.read_text(encoding="utf-8"))

    by_url: dict[str, RawPage] = {}

    def add(pages: list[RawPage]) -> None:
        for page in pages:
            if wave is not None and sites.get(page.site, {}).get("wave") != wave:
                continue
            by_url.setdefault(page.url, page)

    if source in ("raw", "both") and RAW_DIR.is_dir():
        add(fetch_l0.load_raw(RAW_DIR))
    if source in ("rag_memory", "both") and RAG_MEMORY_DIR.is_dir():
        rag_pages = fetch_l0.load_raw(RAG_MEMORY_DIR)
        rag_pages = [page.model_copy(update={"text": _strip_frontmatter(page.text)}) for page in rag_pages]
        add(rag_pages)

    return sorted(by_url.values(), key=lambda page: (page.site, page.url))


def _reset() -> None:
    for path in (settings.DB_PATH, settings.EMB_PATH, Path(f"{settings.EMB_PATH}.ids.json")):
        if path.is_file():
            path.unlink()
            log.info("удалён %s", path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("raw", "rag_memory", "both"), default="both")
    parser.add_argument("--wave", type=int, choices=(1, 2), default=None)
    parser.add_argument("--manual", type=Path, default=None, help="data/conflicts_manual.json")
    parser.add_argument("--reset", action="store_true", help="стереть DB_PATH/EMB_PATH перед индексацией")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if settings.CORPUS != "real":
        log.warning("CORPUS=%s (не 'real') — индексация всё равно пишет в DB_PATH/EMB_PATH", settings.CORPUS)

    if args.reset:
        _reset()

    pages = _load_pages(args.source, args.wave)
    if not pages:
        log.error("Нет страниц для индексации (source=%s, wave=%s)", args.source, args.wave)
        return 1

    conn = store.connect()
    try:
        total_chunks = 0
        all_chunks = []
        sites_seen: set[str] = set()
        for page in pages:
            document_id = chunker.document_id(page.url)
            store.upsert_document(conn, page, document_id)
            page_chunks = chunker.chunk(page)
            inserted = store.upsert_chunks(conn, page_chunks)
            total_chunks += inserted
            all_chunks.extend(page_chunks)
            sites_seen.add(page.site)

        log.info(
            "Документы: %d, сайтов: %d, новых/обновлённых чанков: %d",
            len(pages),
            len(sites_seen),
            total_chunks,
        )

        rows = retrieval.build_index()
        log.info("Эмбеддинги пересчитаны: %d строк -> %s", rows, settings.EMB_PATH)

        # Не используем scout.run() напрямую: его дефолт при отсутствии
        # data/conflicts_manual.json — фикстурный data/fixture/conflicts.json
        # (для fixture-корпуса), который на реальном корпусе не резолвится
        # (другие URL/цитаты) и уронит индексацию. Для real без ручного файла
        # просто нет конфликтов, пока дизайнеры (G1) не заполнят его.
        conflicts = []
        if args.manual is not None and args.manual.exists():
            conflicts = scout_l0.load_manual(args.manual)
        elif args.manual is None:
            default_manual = ROOT / "data" / "conflicts_manual.json"
            if default_manual.exists():
                conflicts = scout_l0.load_manual(default_manual)
        if settings.SCOUT == "llm":
            for group in scout.prefilter(all_chunks):
                conflicts.extend(scout.judge(group, all_chunks))
        conflicts = scout_l0.deduplicate(conflicts)
        for conflict in conflicts:
            store.insert_conflict(conn, conflict)
        log.info("Конфликтов найдено/загружено: %d", len(conflicts))

        stats = store.stats(conn)
        log.info(
            "Итог в БД: документов=%d чанков=%d сайтов=%d конфликтов=%d",
            stats.corpus_documents,
            stats.corpus_chunks,
            stats.sites,
            stats.conflicts,
        )
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

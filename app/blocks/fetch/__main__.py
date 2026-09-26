"""CLI для получения страниц сайтов из data/sites.yaml."""

from __future__ import annotations

import argparse
import logging

import yaml

from app.blocks.fetch import fetch_page, list_urls, save_raw
from app.config import ROOT, settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Скачать страницы сайтов в data/raw")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--site")
    group.add_argument("--wave", type=int, choices=(1, 2))
    parser.add_argument("--limit", type=int, default=150)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sites = yaml.safe_load(settings.SITES_PATH.read_text(encoding="utf-8"))
    if args.site and args.site not in sites:
        parser.error(f"Неизвестный сайт: {args.site}")
    if args.site:
        selected = [args.site]
    else:
        selected = [key for key, value in sites.items() if value.get("wave") == args.wave]
    for site in selected:
        urls = list_urls(site, args.limit)
        saved = skipped = errors = 0
        for url in urls:
            try:
                page = fetch_page(url, site)
                if page is None:
                    skipped += 1
                else:
                    save_raw(page, ROOT / "data" / "raw")
                    saved += 1
            except (OSError, ValueError) as exc:
                logging.warning("Не удалось сохранить %s: %s", url, exc)
                errors += 1
        print(f"{site}: URL {len(urls)}, скачано {saved}, пропущено {skipped}, ошибок {errors}")


if __name__ == "__main__":
    main()

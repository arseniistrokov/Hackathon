"""Сетевое получение страниц I1. Ошибки логируются и возвращаются вызывающему порту."""

from __future__ import annotations

import datetime as dt
import logging
import re
import time
import xml.etree.ElementTree as ET
from collections import deque
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

import httpx
import trafilatura
import yaml

from app.config import settings
from app.contracts.models import RawPage

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "ChisinauAssistant/0.1 (hackathon)"}
SKIP_SUFFIXES = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".bmp",
    ".tif",
    ".tiff",
    ".ico",
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".tgz",
)


def _sites() -> dict[str, dict[str, object]]:
    data = yaml.safe_load(settings.SITES_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _request(client: httpx.Client, url: str) -> httpx.Response:
    error: Exception | None = None
    for attempt in range(2):
        time.sleep(0.3)
        try:
            response = client.get(url)
            if response.status_code == 404:
                return response
            response.raise_for_status()
            return response
        except (httpx.HTTPError, ValueError) as exc:
            error = exc
            if attempt:
                raise
    assert error is not None
    raise error


def _canonical(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def is_wanted(url: str) -> bool:
    parts = urlsplit(url)
    path = parts.path.lower()
    if parts.fragment or re.search(r"/(?:tag|category|author|feed|wp-admin|wp-json)(?:/|$)", path):
        return False
    if "/page/" in path or "replytocom" in parts.query.lower():
        return False
    return not path.endswith(SKIP_SUFFIXES)


def _wp_urls(client: httpx.Client, base: str, limit: int) -> list[str] | None:
    result: list[tuple[str, str | None]] = []
    available = False
    api = urljoin(base, "/wp-json/wp/v2/")
    for endpoint in ("pages", "posts"):
        max_pages = (limit + 99) // 100
        page_number = 1
        while page_number <= max_pages:
            query = f"{endpoint}?per_page=100&page={page_number}&_fields=link,date"
            response = _request(client, urljoin(api, query))
            if response.status_code == 404:
                break
            available = True
            payload = response.json()
            if not isinstance(payload, list):
                break
            if page_number == 1:
                try:
                    max_pages = min(max_pages, max(1, int(response.headers.get("X-WP-TotalPages", "1"))))
                except ValueError:
                    max_pages = 1
            for item in payload:
                if not isinstance(item, dict) or not isinstance(item.get("link"), str):
                    continue
                date = str(item.get("date", ""))[:10] or None
                if date and date < "2023-01-01":
                    continue
                link = _canonical(item["link"])
                if is_wanted(link):
                    result.append((link, date))
            if len(payload) < 100 or len(result) >= limit:
                break
            page_number += 1
        if len(result) >= limit:
            break
    host = urlsplit(base).netloc.lower()
    if not available:
        return None
    return list(dict.fromkeys(url for url, _ in result if urlsplit(url).netloc.lower() == host))[:limit]


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def _page_links(html: str, current: str, host: str) -> list[str]:
    parser = _Links()
    parser.feed(html)
    links: list[str] = []
    for href in parser.links:
        url = _canonical(urljoin(current, href))
        if urlsplit(url).netloc.lower() == host and is_wanted(url):
            links.append(url)
    return links


def _sitemap_urls(client: httpx.Client, base: str, limit: int) -> list[str]:
    sitemap = urljoin(base, "/sitemap.xml")
    response = _request(client, sitemap)
    root = ET.fromstring(response.text)
    locs = [node.text for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "loc" and node.text]
    if root.tag.endswith("sitemapindex"):
        urls: list[str] = []
        for child in locs[:10]:
            child_root = ET.fromstring(_request(client, child).text)
            urls.extend(
                node.text for node in child_root.iter() if node.tag.rsplit("}", 1)[-1] == "loc" and node.text
            )
            if len(urls) >= limit:
                break
        locs = urls
    host = urlsplit(base).netloc.lower()
    urls = (_canonical(url) for url in locs if is_wanted(url))
    return list(dict.fromkeys(url for url in urls if urlsplit(url).netloc.lower() == host))[:limit]


def _bfs(client: httpx.Client, base: str, limit: int) -> list[str]:
    start = _canonical(base)
    host = urlsplit(start).netloc.lower()
    queue = deque([(start, 0)])
    visited: set[str] = set()
    while queue and len(visited) < limit:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        if depth >= 2:
            continue
        try:
            response = _request(client, url)
        except httpx.HTTPError as exc:
            visited.discard(url)
            logger.warning("I1 BFS request failed for %s: %s", url, exc)
            continue
        if "html" not in response.headers.get("content-type", ""):
            continue
        for link in _page_links(response.text, url, host):
            if link not in visited:
                queue.append((link, depth + 1))
    return sorted(visited)


def list_urls(site: str, limit: int = 150) -> list[str]:
    try:
        config = _sites().get(site)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        logger.warning("I1 site configuration unavailable: %s", exc)
        return []
    if not isinstance(config, dict) or not isinstance(config.get("url"), str) or limit < 1:
        return []
    base = str(config["url"])
    try:
        with httpx.Client(timeout=10, follow_redirects=True, headers=HEADERS) as client:
            try:
                wp_urls = _wp_urls(client, base, limit)
                if wp_urls:
                    return wp_urls
            except (httpx.HTTPError, ValueError, OSError) as exc:
                logger.warning("I1 WordPress discovery unavailable for %s: %s", site, exc)
            try:
                urls = _sitemap_urls(client, base, limit)
                if urls:
                    return urls
            except (httpx.HTTPError, ET.ParseError, ValueError) as exc:
                logger.warning("I1 sitemap unavailable for %s: %s", site, exc)
            return _bfs(client, base, limit)[:limit]
    except (httpx.HTTPError, ValueError, OSError) as exc:
        logger.warning("I1 URL discovery failed for %s: %s", site, exc)
        return []


def _wp_page(client: httpx.Client, url: str, site: str, config: dict[str, object]) -> RawPage | None:
    parts = urlsplit(url)
    slug = parts.path.rstrip("/").rsplit("/", maxsplit=1)[-1]
    if not slug:
        return None
    api = f"{parts.scheme}://{parts.netloc}/wp-json/wp/v2/"
    for endpoint in ("pages", "posts"):
        query = f"{endpoint}?slug={quote(slug, safe='')}&_fields=title,content,date,link"
        response = _request(client, urljoin(api, query))
        if response.status_code == 404:
            continue
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            continue
        item = payload[0]
        if not isinstance(item, dict):
            continue
        text = trafilatura.extract(str(item.get("content", {}).get("rendered", ""))) or ""
        if len(text) < 200:
            return None
        title = trafilatura.extract(str(item.get("title", {}).get("rendered", ""))) or ""
        title = title or slug
        return RawPage(
            site=site,
            url=str(item.get("link", url)),
            title=title,
            text=_with_title(text, title),
            category=str(config["category"]),
            date=_date(item.get("date")),
        )
    return None


def _date(value: object) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _with_title(text: str, title: str) -> str:
    heading = f"# {title}"
    return text if text.startswith(heading + "\n") or text == heading else f"{heading}\n\n{text.lstrip()}"


def _language(url: str, html: str) -> str:
    match = re.search(r"<html[^>]*\blang=[\"']([^\"']+)", html, re.IGNORECASE)
    language = match.group(1).lower() if match else ""
    return "ru" if language.startswith("ru") or "/ru/" in urlsplit(url).path.lower() else "ro"


def fetch_page(url: str, site: str) -> RawPage | None:
    try:
        config = _sites().get(site)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        logger.warning("I1 site configuration unavailable: %s", exc)
        return None
    if not isinstance(config, dict):
        return None
    try:
        with httpx.Client(timeout=10, follow_redirects=True, headers=HEADERS) as client:
            try:
                page = _wp_page(client, url, site, config)
                if page:
                    return page
            except (httpx.HTTPError, ValueError, OSError, KeyError, TypeError) as exc:
                logger.warning("I1 WordPress fetch unavailable for %s: %s", url, exc)
            response = _request(client, url)
            is_pdf = "pdf" in response.headers.get("content-type", "")
            is_pdf = is_pdf or urlsplit(url).path.lower().endswith(".pdf")
            if is_pdf:
                import fitz

                with fitz.open(stream=response.content, filetype="pdf") as pdf:
                    text = "\n\n".join(f"[[page {i}]]\n{page.get_text()}" for i, page in enumerate(pdf, 1))
                title = urlsplit(url).path.rsplit("/", maxsplit=1)[-1] or urlsplit(url).netloc
                kind = "pdf"
                lang = "ro"
                date = None
            else:
                extracted = trafilatura.extract(
                    response.text, include_links=False, output_format="markdown", with_metadata=True
                )
                text = extracted or ""
                metadata = trafilatura.extract_metadata(response.text)
                title = (metadata.title if metadata else None) or urlsplit(url).path.rsplit("/", 1)[-1]
                title = title or site
                date = _date(metadata.date if metadata else None)
                kind = "html"
                lang = _language(url, response.text)
            if len(text.strip()) < 200:
                return None
            text = _with_title(text, title)
            return RawPage(
                site=site,
                url=url,
                title=title,
                text=text,
                category=str(config["category"]),
                lang=lang,
                date=date,
                kind=kind,
                fetched_at=dt.datetime.now(dt.UTC),
            )
    except Exception as exc:
        logger.warning("I1 page fetch failed for %s: %s", url, exc)
        return None

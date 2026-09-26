from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

import fitz
import httpx
import pytest
from app.blocks.fetch import __main__ as fetch_cli
from app.blocks.fetch import fetch_page, l1, list_urls, load_raw, save_raw
from app.config import ROOT, settings
from app.contracts.models import RawPage
from docs.references._patterns.backend_block.fixture_loader import load_raw as load_fixture

FIXTURE_ROOT = settings.FIXTURE_DIR / "mini_corpus"
EXPECT = json.loads((settings.FIXTURE_DIR / "expect.json").read_text(encoding="utf-8"))
FIXTURE_PAGES = load_fixture(FIXTURE_ROOT)


def test_load_raw_matches_fixture_counts_and_stable_order() -> None:
    first = load_raw(FIXTURE_ROOT)
    second = load_raw(FIXTURE_ROOT)

    assert len(first) == EXPECT["documents"]
    assert sum(page.lang == "ru" for page in first) == EXPECT["ru_documents"]
    assert sum(page.kind == "pdf" for page in first) == EXPECT["pdf_documents"]
    assert [(page.site, page.url) for page in first] == sorted((page.site, page.url) for page in first)
    assert first == second


@pytest.mark.parametrize("page", FIXTURE_PAGES, ids=lambda page: page.url)
def test_save_raw_round_trips_fixture_page_and_is_idempotent(page: RawPage, tmp_path: Path) -> None:
    saved_path = save_raw(page, tmp_path)
    saved_again = save_raw(page, tmp_path)

    assert saved_path == saved_again
    assert load_raw(tmp_path) == [page]
    assert len(list(tmp_path.rglob("*.meta.json"))) == 1
    assert len(saved_path.stem) <= 80
    assert saved_path.read_text(encoding="utf-8").splitlines()[0] == f"# {page.title}"


def test_unknown_site_returns_empty_without_network() -> None:
    assert list_urls("unknown-site.md") == []
    assert fetch_page("https://rtec.md/", "unknown-site.md") is None


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://site.md/tag/x", False),
        ("https://site.md/page/2", False),
        ("https://site.md/page?replytocom=1", False),
        ("https://site.md/image.jpg", False),
        ("https://site.md/servicii/", True),
        ("https://site.md/contacte", True),
        ("https://site.md/document.pdf", True),
        ("https://site.md/feedback", True),
    ],
)
def test_url_filter(url: str, expected: bool) -> None:
    assert l1.is_wanted(url) is expected


def test_fetch_page_timeout_returns_none_and_logs_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    calls = 0

    class TimeoutClient:
        def __enter__(self) -> TimeoutClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            nonlocal calls
            calls += 1
            raise httpx.TimeoutException("timeout", request=httpx.Request("GET", url))

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: TimeoutClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)

    assert fetch_page("https://rtec.md/program-de-lucru", "rtec.md") is None
    assert calls == 4
    assert "I1 page fetch failed" in caplog.text


def test_request_retries_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    class RetryClient:
        def get(self, url: str) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.TimeoutException("timeout", request=httpx.Request("GET", url))
            return httpx.Response(200, text="ok", request=httpx.Request("GET", url))

    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)

    assert l1._request(RetryClient(), "https://rtec.md/").text == "ok"
    assert calls == 2


def test_fetch_page_extracts_html_without_navigation_or_footer(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_page = next(page for page in FIXTURE_PAGES if page.site == "rtec.md" and len(page.text) > 200)
    html = (
        '<html lang="ro"><head><title>Pagina din fixture</title>'
        '<meta property="article:published_time" content="2024-03-05T12:00:00+00:00"></head>'
        f"<body><nav>MENU_FIXTURE</nav><main><h1>{fixture_page.title}</h1><p>{fixture_page.text}</p>"
        "</main><footer>FOOTER_FIXTURE</footer></body></html>"
    )

    class HtmlClient:
        def __enter__(self) -> HtmlClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            if "/wp-json/" in url:
                return httpx.Response(404, request=httpx.Request("GET", url))
            return httpx.Response(
                200,
                text=html,
                headers={"content-type": "text/html"},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: HtmlClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)
    page = fetch_page(fixture_page.url, fixture_page.site)

    assert page is not None
    assert page.title in {"Pagina din fixture", fixture_page.title}
    assert page.date == fixture_page.date
    assert page.text.splitlines()[0] == f"# {page.title}"
    assert "MENU_FIXTURE" not in page.text
    assert "FOOTER_FIXTURE" not in page.text
    assert fixture_page.text.splitlines()[2][:30] in page.text


def test_fetch_page_parses_wordpress_rest_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_page = next(page for page in FIXTURE_PAGES if page.site == "rtec.md" and len(page.text) > 200)
    payload = [
        {
            "title": {"rendered": f"<strong>{fixture_page.title}</strong>"},
            "content": {"rendered": f"<p>{fixture_page.text}</p>"},
            "date": "2024-03-05T09:00:00",
            "link": fixture_page.url,
        }
    ]

    class WordPressClient:
        def __enter__(self) -> WordPressClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: WordPressClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)
    page = fetch_page(fixture_page.url, fixture_page.site)

    assert page is not None
    assert page.url == fixture_page.url
    assert page.date == fixture_page.date
    assert page.text.splitlines()[0] == f"# {page.title}"
    assert "<p>" not in page.text
    assert "Troleibuzele circulă" in page.text


def test_list_urls_uses_sitemap_after_wordpress_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    first = "https://rtec.md/"
    second = "https://rtec.md/program-de-lucru"

    class SitemapClient:
        def __enter__(self) -> SitemapClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            if "/wp-json/" in url:
                return httpx.Response(404, request=httpx.Request("GET", url))
            xml = (
                f"<urlset><url><loc>{first}</loc></url><url><loc>{second}</loc></url>"
                f"<url><loc>{second}#section</loc></url></urlset>"
            )
            return httpx.Response(200, text=xml, request=httpx.Request("GET", url))

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: SitemapClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)

    expected = [first, second]
    assert list_urls("rtec.md", limit=5) == expected
    assert list_urls("rtec.md", limit=5) == expected


def test_list_urls_uses_wordpress_and_drops_old_or_external_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    class WordPressClient:
        def __enter__(self) -> WordPressClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            if "/pages?" in url:
                payload = [
                    {"link": "https://rtec.md/servicii", "date": "2024-01-01"},
                    {"link": "https://rtec.md/stiri-vechi", "date": "2022-12-31"},
                    {"link": "https://other.md/external", "date": "2024-01-01"},
                ]
                return httpx.Response(200, json=payload, request=httpx.Request("GET", url))
            return httpx.Response(200, json=[], request=httpx.Request("GET", url))

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: WordPressClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)

    assert list_urls("rtec.md", limit=5) == ["https://rtec.md/servicii"]


def test_list_urls_falls_back_to_same_domain_bfs(monkeypatch: pytest.MonkeyPatch) -> None:
    class BfsClient:
        def __enter__(self) -> BfsClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            if "/wp-json/" in url or url.endswith("sitemap.xml"):
                return httpx.Response(404, request=httpx.Request("GET", url))
            path = httpx.URL(url).path
            href = {"/": "/servicii", "/servicii": "/contacte"}.get(path, "/third-level")
            links = f'<a href="{href}">next</a><a href="https://other.md/page">external</a>'
            return httpx.Response(
                200,
                text=f"<html><body>{links}</body></html>",
                headers={"content-type": "text/html"},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: BfsClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)

    expected = [
        "https://rtec.md/",
        "https://rtec.md/contacte",
        "https://rtec.md/servicii",
    ]
    assert list_urls("rtec.md", limit=5) == expected
    assert list_urls("rtec.md", limit=5) == expected


def test_list_urls_returns_empty_and_logs_when_all_discovery_requests_fail(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    class FailedClient:
        def __enter__(self) -> FailedClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            raise httpx.ConnectError("offline", request=httpx.Request("GET", url))

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: FailedClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)

    assert list_urls("rtec.md", limit=5) == []
    assert "I1 BFS request failed" in caplog.text


def test_fetch_page_extracts_pdf_text_with_page_markers(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_page = next(page for page in FIXTURE_PAGES if page.site == "rtec.md" and len(page.text) > 200)
    safe_text = unicodedata.normalize("NFKD", fixture_page.text).encode("ascii", "ignore").decode("ascii")
    document = fitz.open()
    pdf_page = document.new_page()
    pdf_page.insert_textbox(fitz.Rect(30, 30, 560, 780), safe_text, fontsize=8)
    pdf_bytes = document.tobytes()
    document.close()

    class PdfClient:
        def __enter__(self) -> PdfClient:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            if "/wp-json/" in url:
                return httpx.Response(404, request=httpx.Request("GET", url))
            return httpx.Response(
                200,
                content=pdf_bytes,
                headers={"content-type": "application/pdf"},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(l1.httpx, "Client", lambda **_kwargs: PdfClient())
    monkeypatch.setattr(l1.time, "sleep", lambda _seconds: None)
    page = fetch_page("https://rtec.md/fixture.pdf", "rtec.md")

    assert page is not None
    assert page.kind == "pdf"
    assert "[[page 1]]" in page.text
    assert len(page.text) >= 200


def test_cli_downloads_selected_site_to_raw(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fixture_page = next(page for page in FIXTURE_PAGES if page.site == "rtec.md")
    saved: list[tuple[RawPage, Path]] = []
    monkeypatch.setattr(sys, "argv", ["fetch", "--site", fixture_page.site, "--limit", "3"])
    monkeypatch.setattr(fetch_cli, "list_urls", lambda _site, _limit: [fixture_page.url])
    monkeypatch.setattr(fetch_cli, "fetch_page", lambda _url, _site: fixture_page)
    monkeypatch.setattr(
        fetch_cli, "save_raw", lambda page, root: saved.append((page, root)) or root / "page.md"
    )

    fetch_cli.main()

    assert saved == [(fixture_page, ROOT / "data" / "raw")]
    assert "rtec.md: URL 1, скачано 1, пропущено 0, ошибок 0" in capsys.readouterr().out

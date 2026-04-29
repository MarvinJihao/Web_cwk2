"""Website crawler for the quotes search tool."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
import re
from time import sleep
from typing import Callable, Iterable
from urllib.parse import urldefrag, urljoin, urlparse


@dataclass(frozen=True)
class Page:
    """A crawled page and the text that should be indexed."""

    url: str
    text: str
    title: str = ""
    status: int = 200
    content_hash: str = ""


@dataclass(frozen=True)
class CrawlFailure:
    """Details of a URL that could not be crawled."""

    url: str
    error: str
    status: int | None = None


class _FallbackHTMLParser(HTMLParser):
    """Small fallback parser used when BeautifulSoup is unavailable."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)


class Crawler:
    """Crawl pages from one website while respecting a politeness delay."""

    def __init__(
        self,
        start_url: str,
        *,
        politeness_delay: float = 6.0,
        session: object | None = None,
        sleeper: Callable[[float], None] = sleep,
        timeout: float = 10.0,
        url_filter: Callable[[str], bool] | None = None,
    ) -> None:
        self.start_url = self._normalise_url(start_url)
        self.politeness_delay = politeness_delay
        self.session = session or self._default_session()
        self.sleeper = sleeper
        self.timeout = timeout
        self.url_filter = url_filter
        self._start_netloc = urlparse(self.start_url).netloc
        self.failures: list[CrawlFailure] = []

    def crawl(
        self,
        *,
        max_pages: int | None = None,
        on_page_crawled: Callable[[int, str], None] | None = None,
        on_page_failed: Callable[[int, str, str], None] | None = None,
    ) -> list[Page]:
        """Crawl internal pages breadth-first and return page text."""

        queue: deque[str] = deque([self.start_url])
        seen: set[str] = set()
        queued: set[str] = {self.start_url}
        content_hashes: set[str] = set()
        pages: list[Page] = []
        request_count = 0
        self.failures = []

        while queue and (max_pages is None or len(pages) < max_pages):
            url = queue.popleft()
            queued.discard(url)
            if url in seen:
                continue

            if request_count > 0 and self.politeness_delay > 0:
                self.sleeper(self.politeness_delay)

            request_count += 1
            seen.add(url)
            try:
                html, status = self._fetch(url)
            except Exception as exc:
                response = getattr(exc, "response", None)
                failure = CrawlFailure(
                    url=url,
                    error=str(exc),
                    status=getattr(response, "status_code", None),
                )
                self.failures.append(failure)
                if on_page_failed is not None:
                    on_page_failed(len(self.failures), url, failure.error)
                continue

            text, links, title = self._parse_html(html)
            content_hash = self._hash_text(text)
            if content_hash and content_hash not in content_hashes:
                content_hashes.add(content_hash)
                pages.append(
                    Page(
                        url=url,
                        text=text,
                        title=title,
                        status=status,
                        content_hash=content_hash,
                    )
                )
            if on_page_crawled is not None and (not content_hash or content_hash in content_hashes):
                on_page_crawled(len(pages), url)

            for link in self._normalise_links(url, links):
                if link not in seen and link not in queued:
                    queue.append(link)
                    queued.add(link)

        return pages

    def _fetch(self, url: str) -> tuple[str, int]:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text, int(getattr(response, "status_code", 200))

    def _parse_html(self, html: str) -> tuple[str, list[str], str]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            parser = _FallbackHTMLParser()
            parser.feed(html)
            return " ".join(parser.text_parts), parser.links, ""

        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style"]):
            element.decompose()
        text = soup.get_text(" ", strip=True)
        links = [anchor["href"] for anchor in soup.find_all("a", href=True)]
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        return text, links, title

    def _normalise_links(self, current_url: str, links: Iterable[str]) -> list[str]:
        normalised: list[str] = []
        for link in links:
            absolute = self._normalise_url(urljoin(current_url, link))
            parsed = urlparse(absolute)
            if (
                parsed.scheme in {"http", "https"}
                and parsed.netloc == self._start_netloc
                and (self.url_filter is None or self.url_filter(absolute))
            ):
                normalised.append(absolute)
        return normalised

    @staticmethod
    def _normalise_url(url: str) -> str:
        url, _fragment = urldefrag(url)
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        url = f"{scheme}://{netloc}{path}"
        if url.endswith("/page/1/") or url.endswith("/page/1"):
            return url[: url.rfind("/page/1")].rstrip("/") or url
        return url.rstrip("/") or url

    @staticmethod
    def _hash_text(text: str) -> str:
        normalised = re.sub(r"\s+", " ", text).strip().lower()
        if not normalised:
            return ""
        return sha256(normalised.encode("utf-8")).hexdigest()

    @staticmethod
    def _default_session() -> object:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "The requests package is required for live crawling. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from exc
        return requests.Session()

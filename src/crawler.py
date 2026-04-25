"""Website crawler for the quotes search tool."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from time import sleep
from typing import Callable, Iterable
from urllib.parse import urldefrag, urljoin, urlparse


@dataclass(frozen=True)
class Page:
    """A crawled page and the text that should be indexed."""

    url: str
    text: str


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
    ) -> None:
        self.start_url = self._normalise_url(start_url)
        self.politeness_delay = politeness_delay
        self.session = session or self._default_session()
        self.sleeper = sleeper
        self.timeout = timeout
        self._start_netloc = urlparse(self.start_url).netloc

    def crawl(self, *, max_pages: int | None = None) -> list[Page]:
        """Crawl internal pages breadth-first and return page text."""

        queue: deque[str] = deque([self.start_url])
        seen: set[str] = set()
        pages: list[Page] = []
        request_count = 0

        while queue and (max_pages is None or len(pages) < max_pages):
            url = queue.popleft()
            if url in seen:
                continue

            if request_count > 0 and self.politeness_delay > 0:
                self.sleeper(self.politeness_delay)

            html = self._fetch(url)
            request_count += 1
            seen.add(url)

            text, links = self._parse_html(html)
            pages.append(Page(url=url, text=text))

            for link in self._normalise_links(url, links):
                if link not in seen:
                    queue.append(link)

        return pages

    def _fetch(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def _parse_html(self, html: str) -> tuple[str, list[str]]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            parser = _FallbackHTMLParser()
            parser.feed(html)
            return " ".join(parser.text_parts), parser.links

        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style"]):
            element.decompose()
        text = soup.get_text(" ", strip=True)
        links = [anchor["href"] for anchor in soup.find_all("a", href=True)]
        return text, links

    def _normalise_links(self, current_url: str, links: Iterable[str]) -> list[str]:
        normalised: list[str] = []
        for link in links:
            absolute = self._normalise_url(urljoin(current_url, link))
            parsed = urlparse(absolute)
            if parsed.scheme in {"http", "https"} and parsed.netloc == self._start_netloc:
                normalised.append(absolute)
        return normalised

    @staticmethod
    def _normalise_url(url: str) -> str:
        url, _fragment = urldefrag(url)
        return url.rstrip("/") or url

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


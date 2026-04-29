"""Command-line shell for the coursework search tool."""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from urllib.parse import urlparse

from src.crawler import Crawler
from src.indexer import InvertedIndex
from src.search import SearchEngine
from src.storage import load_index, save_index

DEFAULT_START_URL = "https://quotes.toscrape.com/"
DEFAULT_INDEX_PATH = Path("data/index.json")


class SearchShell:
    """Interactive shell exposing build, load, print and find commands."""

    def __init__(
        self,
        *,
        start_url: str = DEFAULT_START_URL,
        index_path: Path = DEFAULT_INDEX_PATH,
        politeness_delay: float = 6.0,
    ) -> None:
        self.start_url = start_url
        self.index_path = index_path
        self.politeness_delay = politeness_delay
        self.index: InvertedIndex | None = None

    def run(self) -> None:
        print("Search tool ready. Commands: build, load, print <word>, find <query>, exit")
        while True:
            try:
                raw_command = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return

            if not raw_command:
                continue
            if raw_command in {"exit", "quit"}:
                return

            try:
                output = self.handle(raw_command)
            except Exception as exc:
                output = f"Error: {exc}"
            if output:
                print(output)

    def handle(self, raw_command: str) -> str:
        parts = shlex.split(raw_command)
        if not parts:
            return ""
        command = parts[0].lower()
        args = parts[1:]

        if command == "build":
            return self._build()
        if command == "load":
            return self._load()
        if command == "print":
            return self._print(args)
        if command == "find":
            return self._find(args)
        if command == "help":
            return "Commands: build, load, print <word>, find <query>, exit"
        return f"Unknown command: {command}"

    def _build(self) -> str:
        crawler = Crawler(
            self.start_url,
            politeness_delay=self.politeness_delay,
            url_filter=self._should_crawl_url,
        )
        print("Building index. This waits 6 seconds between page requests...", flush=True)
        pages = crawler.crawl(on_page_crawled=self._print_crawl_progress)
        index = InvertedIndex()
        index.build(pages)
        save_index(index, self.index_path)
        self.index = index
        return f"Built index for {len(pages)} pages and saved it to {self.index_path}"

    def _load(self) -> str:
        self.index = load_index(self.index_path)
        return f"Loaded index from {self.index_path}"

    def _print(self, args: list[str]) -> str:
        if not args:
            return "Usage: print <word>"
        engine = self._engine()
        postings = engine.print_word(args[0])
        if not postings:
            return "No entries found."
        return json.dumps(postings, indent=2, sort_keys=True)

    def _find(self, args: list[str]) -> str:
        if not args:
            return "Usage: find <query>"
        engine = self._engine()
        results = engine.find(" ".join(args))
        if not results:
            return "No pages found."
        return "\n".join(f"{result.url} (score: {result.score})" for result in results)

    def _engine(self) -> SearchEngine:
        if self.index is None:
            raise RuntimeError("No index loaded. Run build or load first.")
        return SearchEngine(self.index)

    @staticmethod
    def _should_crawl_url(url: str) -> bool:
        path = urlparse(url).path
        return path in {"", "/"} or path.startswith("/page/")

    @staticmethod
    def _print_crawl_progress(page_count: int, url: str) -> None:
        print(f"Crawled {page_count}: {url}", flush=True)


def main() -> None:
    SearchShell().run()


if __name__ == "__main__":
    main()

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
            return self._build(args)
        if command == "load":
            return self._load()
        if command == "print":
            return self._print(args)
        if command == "find":
            return self._find(args)
        if command == "help":
            return "Commands: build, load, print <word>, find <query>, exit"
        return f"Unknown command: {command}"

    def _build(self, args: list[str] | None = None) -> str:
        max_pages = self._parse_max_pages(args or [])
        crawler = Crawler(
            self.start_url,
            politeness_delay=self.politeness_delay,
            url_filter=self._should_crawl_url,
        )
        print("Building index. This waits 6 seconds between page requests...", flush=True)
        pages = crawler.crawl(
            max_pages=max_pages,
            on_page_crawled=self._print_crawl_progress,
            on_page_failed=self._print_crawl_failure,
        )
        index = InvertedIndex()
        index.build(pages)
        save_index(index, self.index_path)
        self.index = index
        return (
            f"Built index for {len(pages)} pages with {len(crawler.failures)} failed requests "
            f"and saved it to {self.index_path}"
        )

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
            return "Usage: find [all|any] <query>"
        engine = self._engine()
        mode = "all"
        query_parts = args
        if args[0].lower() in {"all", "any"}:
            mode = args[0].lower()
            query_parts = args[1:]
        if not query_parts:
            return "Usage: find [all|any] <query>"

        phrase = any(" " in part for part in query_parts)
        query = " ".join(query_parts)
        results = engine.find(query, mode=mode, phrase=phrase)
        if not results:
            suggestions = engine.suggest(query)
            if not suggestions:
                return "No pages found."
            suggestion_lines = [
                f"Did you mean {', '.join(matches)} for '{term}'?"
                for term, matches in suggestions.items()
            ]
            return "No pages found.\n" + "\n".join(suggestion_lines)
        return "\n".join(self._format_result(result) for result in results)

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

    @staticmethod
    def _print_crawl_failure(failure_count: int, url: str, error: str) -> None:
        print(f"Warning {failure_count}: skipped {url} ({error})", flush=True)

    @staticmethod
    def _parse_max_pages(args: list[str]) -> int | None:
        if not args:
            return None
        if len(args) == 2 and args[0] == "--max-pages":
            max_pages = int(args[1])
            if max_pages < 1:
                raise ValueError("--max-pages must be at least 1")
            return max_pages
        raise ValueError("Usage: build [--max-pages N]")

    @staticmethod
    def _format_result(result: object) -> str:
        url = getattr(result, "url")
        score = getattr(result, "score")
        title = getattr(result, "title", "")
        if title:
            return f"{url} - {title} (score: {score:.4f})"
        return f"{url} (score: {score:.4f})"


def main() -> None:
    SearchShell().run()


if __name__ == "__main__":
    main()

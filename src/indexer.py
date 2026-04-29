"""Inverted index construction."""

from __future__ import annotations

import re
from typing import Iterable, cast

from src.crawler import Page

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def tokenize(text: str) -> list[str]:
    """Split text into case-insensitive searchable words."""

    return TOKEN_RE.findall(text.lower())


class InvertedIndex:
    """Stores word statistics for each crawled page."""

    def __init__(self) -> None:
        self.documents: dict[str, dict[str, int | str]] = {}
        self.terms: dict[str, dict[str, object]] = {}

    def add_document(
        self,
        url: str,
        text: str,
        *,
        title: str = "",
        status: int = 200,
        content_hash: str = "",
    ) -> None:
        tokens = tokenize(text)
        self.documents[url] = {
            "url": url,
            "title": title,
            "status": status,
            "word_count": len(tokens),
            "content_hash": content_hash,
        }

        for position, token in enumerate(tokens):
            term_entry = self.terms.setdefault(token, {"document_frequency": 0, "postings": {}})
            postings = cast(dict[str, dict[str, list[int] | int]], term_entry["postings"])
            if url not in postings:
                term_entry["document_frequency"] = int(term_entry["document_frequency"]) + 1
            stats = postings.setdefault(url, {"frequency": 0, "positions": []})
            stats["frequency"] = int(stats["frequency"]) + 1
            positions = stats["positions"]
            if isinstance(positions, list):
                positions.append(position)

    def build(self, pages: Iterable[Page]) -> None:
        for page in pages:
            self.add_document(
                page.url,
                page.text,
                title=page.title,
                status=page.status,
                content_hash=page.content_hash,
            )

    def postings_for(self, word: str) -> dict[str, dict[str, list[int] | int]]:
        tokens = tokenize(word)
        if not tokens:
            return {}
        term_entry = self.terms.get(tokens[0])
        if not term_entry:
            return {}
        return cast(dict[str, dict[str, list[int] | int]], term_entry["postings"])

    def document_frequency(self, word: str) -> int:
        tokens = tokenize(word)
        if not tokens:
            return 0
        term_entry = self.terms.get(tokens[0])
        if not term_entry:
            return 0
        return int(term_entry["document_frequency"])

    def vocabulary(self) -> list[str]:
        return sorted(self.terms)

    def to_dict(self) -> dict[str, object]:
        return {
            "documents": self.documents,
            "terms": self.terms,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "InvertedIndex":
        inverted_index = cls()
        inverted_index.documents = dict(payload.get("documents", {}))
        if "terms" in payload:
            inverted_index.terms = dict(payload.get("terms", {}))
        else:
            old_index = cast(dict[str, dict[str, dict[str, list[int] | int]]], payload.get("index", {}))
            inverted_index.terms = {
                term: {
                    "document_frequency": len(postings),
                    "postings": postings,
                }
                for term, postings in old_index.items()
            }
        return inverted_index

"""Inverted index construction."""

from __future__ import annotations

import re
from typing import Iterable

from src.crawler import Page

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def tokenize(text: str) -> list[str]:
    """Split text into case-insensitive searchable words."""

    return TOKEN_RE.findall(text.lower())


class InvertedIndex:
    """Stores word statistics for each crawled page."""

    def __init__(self) -> None:
        self.documents: dict[str, dict[str, int]] = {}
        self.index: dict[str, dict[str, dict[str, list[int] | int]]] = {}

    def add_document(self, url: str, text: str) -> None:
        tokens = tokenize(text)
        self.documents[url] = {"word_count": len(tokens)}

        for position, token in enumerate(tokens):
            postings = self.index.setdefault(token, {})
            stats = postings.setdefault(url, {"frequency": 0, "positions": []})
            stats["frequency"] = int(stats["frequency"]) + 1
            positions = stats["positions"]
            if isinstance(positions, list):
                positions.append(position)

    def build(self, pages: Iterable[Page]) -> None:
        for page in pages:
            self.add_document(page.url, page.text)

    def postings_for(self, word: str) -> dict[str, dict[str, list[int] | int]]:
        tokens = tokenize(word)
        if not tokens:
            return {}
        return self.index.get(tokens[0], {})

    def to_dict(self) -> dict[str, object]:
        return {
            "documents": self.documents,
            "index": self.index,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "InvertedIndex":
        inverted_index = cls()
        inverted_index.documents = dict(payload.get("documents", {}))
        inverted_index.index = dict(payload.get("index", {}))
        return inverted_index

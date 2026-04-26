"""Search operations over the inverted index."""

from __future__ import annotations

from dataclasses import dataclass

from src.indexer import InvertedIndex, tokenize


@dataclass(frozen=True)
class SearchResult:
    url: str
    score: int


class SearchEngine:
    """Query helper for print and find commands."""

    def __init__(self, index: InvertedIndex) -> None:
        self.index = index

    def print_word(self, word: str) -> dict[str, dict[str, list[int] | int]]:
        return self.index.postings_for(word)

    def find(self, query: str) -> list[SearchResult]:
        terms = tokenize(query)
        if not terms:
            return []

        postings_by_term = [self.index.postings_for(term) for term in terms]
        if any(not postings for postings in postings_by_term):
            return []

        matching_urls = set(postings_by_term[0])
        for postings in postings_by_term[1:]:
            matching_urls &= set(postings)

        results: list[SearchResult] = []
        for url in matching_urls:
            score = 0
            for postings in postings_by_term:
                score += int(postings[url]["frequency"])
            results.append(SearchResult(url=url, score=score))

        return sorted(results, key=lambda result: (-result.score, result.url))


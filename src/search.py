"""Search operations over the inverted index."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from math import log

from src.indexer import InvertedIndex, tokenize


@dataclass(frozen=True)
class SearchResult:
    url: str
    score: float
    title: str = ""


class SearchEngine:
    """Query helper for print and find commands."""

    def __init__(self, index: InvertedIndex) -> None:
        self.index = index

    def print_word(self, word: str) -> dict[str, dict[str, list[int] | int]]:
        return self.index.postings_for(word)

    def find(self, query: str, *, mode: str = "all", phrase: bool = False) -> list[SearchResult]:
        terms = tokenize(query)
        if not terms:
            return []

        postings_by_term = [self.index.postings_for(term) for term in terms]
        if any(not postings for postings in postings_by_term):
            return []

        if phrase and len(terms) > 1:
            matching_urls = self._phrase_matching_urls(terms, postings_by_term)
        elif mode == "any":
            matching_urls = set().union(*(set(postings) for postings in postings_by_term))
        else:
            matching_urls = set(postings_by_term[0])
            for postings in postings_by_term[1:]:
                matching_urls &= set(postings)

        results: list[SearchResult] = []
        for url in matching_urls:
            score = self._tf_idf_score(url, terms)
            title = str(self.index.documents.get(url, {}).get("title", ""))
            results.append(SearchResult(url=url, score=score, title=title))

        return sorted(results, key=lambda result: (-result.score, result.url))

    def suggest(self, query: str, *, limit: int = 3) -> dict[str, list[str]]:
        suggestions: dict[str, list[str]] = {}
        vocabulary = self.index.vocabulary()
        for term in tokenize(query):
            if self.index.document_frequency(term) == 0:
                matches = get_close_matches(term, vocabulary, n=limit, cutoff=0.75)
                if matches:
                    suggestions[term] = matches
        return suggestions

    def _tf_idf_score(self, url: str, terms: list[str]) -> float:
        total_documents = max(len(self.index.documents), 1)
        score = 0.0
        for term in terms:
            postings = self.index.postings_for(term)
            stats = postings.get(url)
            if not stats:
                continue
            term_frequency = int(stats["frequency"])
            inverse_document_frequency = log((1 + total_documents) / (1 + self.index.document_frequency(term))) + 1
            score += term_frequency * inverse_document_frequency
        return score

    @staticmethod
    def _phrase_matching_urls(
        terms: list[str],
        postings_by_term: list[dict[str, dict[str, list[int] | int]]],
    ) -> set[str]:
        matching_urls = set(postings_by_term[0])
        for postings in postings_by_term[1:]:
            matching_urls &= set(postings)

        phrase_urls: set[str] = set()
        for url in matching_urls:
            first_positions = postings_by_term[0][url]["positions"]
            if not isinstance(first_positions, list):
                continue
            other_positions = []
            for postings in postings_by_term[1:]:
                positions = postings[url]["positions"]
                if not isinstance(positions, list):
                    break
                other_positions.append(set(positions))
            else:
                for start in first_positions:
                    if all((start + offset) in positions for offset, positions in enumerate(other_positions, start=1)):
                        phrase_urls.add(url)
                        break
        return phrase_urls

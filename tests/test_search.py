from src.indexer import InvertedIndex
from src.search import SearchEngine


def make_engine():
    index = InvertedIndex()
    index.add_document("https://example.com/1", "good friends and good books")
    index.add_document("https://example.com/2", "good ideas")
    index.add_document("https://example.com/3", "quiet indifference")
    return SearchEngine(index)


def test_find_returns_pages_containing_one_term_ranked_by_frequency():
    results = make_engine().find("good")

    assert [result.url for result in results] == [
        "https://example.com/1",
        "https://example.com/2",
    ]
    assert [result.score for result in results] == [2, 1]


def test_find_returns_pages_containing_all_terms():
    results = make_engine().find("good friends")

    assert [result.url for result in results] == ["https://example.com/1"]


def test_find_handles_empty_and_missing_queries():
    engine = make_engine()

    assert engine.find("") == []
    assert engine.find("notfound") == []


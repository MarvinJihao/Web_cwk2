from src.indexer import InvertedIndex
from src.search import SearchEngine
from tests.search_helpers import make_engine


def test_find_supports_phrase_queries():
    engine = make_engine()

    assert [result.url for result in engine.find("good friends", phrase=True)] == [
        "https://example.com/1"
    ]
    assert engine.find("friends good", phrase=True) == []


def test_phrase_search_uses_positions():
    index = InvertedIndex()
    index.add_document("https://example.com/1", "good books and friends")
    index.add_document("https://example.com/2", "good friends and books")
    engine = SearchEngine(index)

    all_results = engine.find("good friends")
    phrase_results = engine.find("good friends", phrase=True)

    assert [result.url for result in all_results] == [
        "https://example.com/1",
        "https://example.com/2",
    ]
    assert [result.url for result in phrase_results] == ["https://example.com/2"]

from tests.search_helpers import make_engine


def test_find_returns_pages_containing_one_term_ranked_by_frequency():
    results = make_engine().find("good")

    assert [result.url for result in results] == [
        "https://example.com/1",
        "https://example.com/2",
    ]
    assert results[0].score > results[1].score
    assert results[0].title == "Books"


def test_find_handles_empty_and_missing_queries():
    engine = make_engine()

    assert engine.find("") == []
    assert engine.find("notfound") == []

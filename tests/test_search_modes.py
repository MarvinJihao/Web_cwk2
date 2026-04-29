from tests.search_helpers import make_engine


def test_find_returns_pages_containing_all_terms():
    results = make_engine().find("good friends")

    assert [result.url for result in results] == ["https://example.com/1"]


def test_find_all_requires_all_terms():
    engine = make_engine()

    results = engine.find("good indifference", mode="all")

    assert results == []


def test_find_supports_any_mode():
    results = make_engine().find("friends ideas", mode="any")

    assert [result.url for result in results] == [
        "https://example.com/1",
        "https://example.com/2",
    ]


def test_find_any_allows_any_term():
    engine = make_engine()

    results = engine.find("friends indifference", mode="any")

    assert [result.url for result in results] == [
        "https://example.com/1",
        "https://example.com/3",
    ]

from tests.search_helpers import make_engine


def test_suggest_returns_close_vocabulary_matches():
    suggestions = make_engine().suggest("indiference")

    assert suggestions == {"indiference": ["indifference"]}


def test_spelling_suggestion_for_unknown_word():
    engine = make_engine()

    suggestions = engine.suggest("freinds indiference")

    assert suggestions == {
        "freinds": ["friends"],
        "indiference": ["indifference"],
    }

from src.indexer import InvertedIndex, tokenize


def test_tokenize_is_case_insensitive_and_ignores_punctuation():
    assert tokenize("Good, good! Friends.") == ["good", "good", "friends"]


def test_indexer_stores_frequency_and_positions():
    index = InvertedIndex()

    index.add_document("https://example.com/1", "Good friends are good")

    assert index.documents["https://example.com/1"]["word_count"] == 4
    assert index.postings_for("GOOD") == {
        "https://example.com/1": {"frequency": 2, "positions": [0, 3]}
    }


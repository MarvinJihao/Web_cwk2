from src.indexer import InvertedIndex, tokenize


def test_tokenize_is_case_insensitive_and_ignores_punctuation():
    assert tokenize("Good, good! Friends.") == ["good", "good", "friends"]


def test_indexer_stores_frequency_and_positions():
    index = InvertedIndex()

    index.add_document(
        "https://example.com/1",
        "Good friends are good",
        title="Example",
        status=200,
        content_hash="abc123",
    )

    assert index.documents["https://example.com/1"]["word_count"] == 4
    assert index.documents["https://example.com/1"]["title"] == "Example"
    assert index.documents["https://example.com/1"]["status"] == 200
    assert index.documents["https://example.com/1"]["content_hash"] == "abc123"
    assert index.postings_for("GOOD") == {
        "https://example.com/1": {"frequency": 2, "positions": [0, 3]}
    }
    assert index.document_frequency("good") == 1


def test_indexer_exports_terms_with_document_frequency():
    index = InvertedIndex()

    index.add_document("https://example.com/1", "good friends")
    index.add_document("https://example.com/2", "good ideas")

    payload = index.to_dict()

    assert payload["terms"]["good"]["document_frequency"] == 2
    assert index.vocabulary() == ["friends", "good", "ideas"]

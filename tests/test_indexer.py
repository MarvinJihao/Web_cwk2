from src.crawler import Page
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


def test_index_can_be_saved_and_loaded(tmp_path):
    index = InvertedIndex()
    index.build([Page(url="https://example.com", text="simple quote")])
    path = tmp_path / "index.json"

    index.save(path)
    loaded = InvertedIndex.load(path)

    assert loaded.to_dict() == index.to_dict()


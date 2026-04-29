from src.crawler import Page
from src.indexer import InvertedIndex
from src.storage import load_index, save_index


def test_index_can_be_saved_and_loaded(tmp_path):
    index = InvertedIndex()
    index.build(
        [
            Page(
                url="https://example.com",
                text="simple quote",
                title="Example",
                status=200,
                content_hash="abc123",
            )
        ]
    )
    path = tmp_path / "index.json"

    save_index(index, path)
    loaded = load_index(path)

    assert loaded.to_dict() == index.to_dict()


def test_old_index_shape_can_still_be_loaded():
    payload = {
        "documents": {"https://example.com": {"word_count": 1}},
        "index": {"quote": {"https://example.com": {"frequency": 1, "positions": [0]}}},
    }

    loaded = InvertedIndex.from_dict(payload)

    assert loaded.document_frequency("quote") == 1
    assert loaded.postings_for("quote") == {
        "https://example.com": {"frequency": 1, "positions": [0]}
    }

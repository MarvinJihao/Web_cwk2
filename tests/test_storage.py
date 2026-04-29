from src.crawler import Page
from src.indexer import InvertedIndex
from src.storage import load_index, save_index


def test_index_can_be_saved_and_loaded(tmp_path):
    index = InvertedIndex()
    index.build([Page(url="https://example.com", text="simple quote")])
    path = tmp_path / "index.json"

    save_index(index, path)
    loaded = load_index(path)

    assert loaded.to_dict() == index.to_dict()

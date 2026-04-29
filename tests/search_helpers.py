from src.indexer import InvertedIndex
from src.search import SearchEngine


def make_engine():
    index = InvertedIndex()
    index.add_document("https://example.com/1", "good friends and good books", title="Books")
    index.add_document("https://example.com/2", "good ideas", title="Ideas")
    index.add_document("https://example.com/3", "quiet indifference")
    return SearchEngine(index)

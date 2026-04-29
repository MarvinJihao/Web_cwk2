# COMP3011 Coursework 2 Search Tool

Python command-line search tool for `https://quotes.toscrape.com/`.

The tool crawls the target website, builds an inverted index of word occurrences, saves the index to disk, loads it later, prints postings for a word, and finds pages containing one or more query terms.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Start the interactive shell:

```bash
python -m src.main
```

Available commands:

```text
> build
> load
> print nonsense
> find indifference
> find good friends
> exit
```

`build` crawls the website with a 6 second politeness delay between successive requests and saves the compiled index to `data/index.json`.

`load` reads `data/index.json` back from disk.

`print <word>` shows the inverted-index postings for one word, including frequency and positions per page.

`find <query>` returns pages that contain all query terms, ranked by total term frequency.

## Project Structure

```text
src/
  crawler.py
  indexer.py
  search.py
  storage.py
  main.py
tests/
  test_crawler.py
  test_indexer.py
  test_search.py
  test_storage.py
data/
  index.json
requirements.txt
README.md
```

## Testing

```bash
pytest
```

The tests use fake crawler responses, so they do not access the live website and do not wait for the real 6 second politeness delay.

## Design Notes

The inverted index uses this shape:

```json
{
  "word": {
    "page-url": {
      "frequency": 2,
      "positions": [0, 3]
    }
  }
}
```

This keeps `print` simple and lets `find` intersect page sets for multi-word queries. Search is case-insensitive, matching the coursework brief.

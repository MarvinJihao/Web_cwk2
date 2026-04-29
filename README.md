# COMP3011 Coursework 2 Search Tool

Python command-line search tool for `https://quotes.toscrape.com/`.

The tool crawls the target website, builds an inverted index of word occurrences, saves the index to disk, loads it later, prints postings for a word, and finds pages containing query terms. Search is case-insensitive and uses TF-IDF ranking.

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
> build --max-pages 10
> load
> print nonsense
> find indifference
> find good friends
> find any good friends
> find all good friends
> find "good friends"
> exit
```

`build` crawls the quote listing pages from `https://quotes.toscrape.com/` by following the homepage and `/page/...` pagination links. It waits at least 6 seconds between successive requests, de-duplicates canonical URLs and duplicate page text, and saves the index to `data/index.json`. If a request fails, the crawler prints a warning, records the failed URL, and continues crawling.

`build --max-pages N` is useful for quick development runs. The normal `build` command follows pagination until no new eligible quote listing pages remain.

`load` reads `data/index.json` back from disk.

`print <word>` shows the postings for one word, including frequency and positions per page.

`find <query>` defaults to `all` mode and returns pages containing every query term. `find any <query>` returns pages containing at least one term. Quoted input, such as `find "good friends"`, is treated as a phrase search and requires consecutive token positions. If no pages match, the tool suggests close vocabulary matches when possible.

## Project Structure

```text
src/
  crawler.py      # HTTP requests, link parsing, politeness, errors, de-duplication
  indexer.py      # tokenisation, normalisation, inverted index, document frequency
  search.py       # print/find, TF-IDF ranking, phrase search, query suggestions
  storage.py      # JSON save/load
  main.py         # interactive command shell
tests/
  helpers.py
  search_helpers.py
  test_crawler_core.py
  test_crawler_canonicalisation.py
  test_crawler_resilience.py
  test_indexer.py
  test_main.py
  test_search_modes.py
  test_search_phrase.py
  test_search_ranking.py
  test_search_suggestions.py
  test_storage.py
data/
  index.json
requirements.txt
README.md
```

## Architecture

The crawler performs a breadth-first crawl over quote listing pages. It follows the homepage and `/page/...` links while ignoring author, tag, login, and external links. URLs are normalised by removing fragments, lower-casing the scheme and host, trimming trailing slashes, and treating `/page/1` as the homepage. Page text is hashed after whitespace normalisation so duplicate content is indexed once.

The index stores document metadata and term statistics:

```json
{
  "documents": {
    "https://quotes.toscrape.com": {
      "url": "https://quotes.toscrape.com",
      "title": "Quotes to Scrape",
      "status": 200,
      "word_count": 123,
      "content_hash": "..."
    }
  },
  "terms": {
    "good": {
      "document_frequency": 5,
      "postings": {
        "https://quotes.toscrape.com": {
          "frequency": 2,
          "positions": [10, 42]
        }
      }
    }
  }
}
```

This structure keeps `print` simple, supports phrase search through token positions, and supports TF-IDF ranking through document frequency.

## Ranking

Search results are ranked with:

```text
score(page, query) = sum(tf(term, page) * idf(term))
idf(term) = log((1 + total_documents) / (1 + document_frequency(term))) + 1
```

The smoothing avoids division by zero and keeps rare terms more influential than common terms.

## Testing

Run the tests:

```bash
python -m pytest -q -p no:cacheprovider
```

The tests use fake crawler responses, so they do not access the live website and do not wait for the real 6 second politeness delay.

The suite is split by behaviour so each coursework requirement is easy to audit:

```text
tests/test_crawler_core.py              link discovery, metadata extraction, filtering, politeness
tests/test_crawler_canonicalisation.py  /page/1 canonicalisation and duplicate URL prevention
tests/test_crawler_resilience.py        failed-request recovery and duplicate content hashing
tests/test_indexer.py                   tokenisation, metadata, postings, positions, document frequency
tests/test_main.py                      default crawl boundary for quote listing pages
tests/test_search_modes.py              ALL and ANY query semantics
tests/test_search_phrase.py             phrase queries using token positions
tests/test_search_ranking.py            TF-IDF ordering and empty/missing query handling
tests/test_search_suggestions.py        spelling suggestions for unknown terms
tests/test_storage.py                   JSON save/load and backward-compatible index loading
```

The tests use `FakeSession` and small in-memory indexes so they are deterministic, fast, and independent of the live website. This also means the crawler politeness behaviour can be verified without actually waiting six seconds during the test run.

## Design Notes

- The crawler intentionally indexes quote listing pages rather than author, tag, and login pages. This keeps the index focused on quote content and avoids long crawls caused by many tag/author links.
- The crawler continues after network or HTTP errors. This is safer than aborting the whole build because one failed page should not destroy the compiled index.
- The saved index is a single JSON file for simplicity and transparency.
- The implementation favours standard Python data structures so the data model can be explained clearly in the video demonstration.

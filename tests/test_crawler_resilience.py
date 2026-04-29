from src.crawler import Crawler
from tests.helpers import FakeSession


def test_crawler_skips_failed_pages_and_continues():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": """
                <a href="/missing/">missing</a>
                <a href="/page/2/">next</a>
            """,
            "https://quotes.toscrape.com/page/2": "Done",
        }
    )
    failures = []

    crawler = Crawler(
        "https://quotes.toscrape.com/",
        politeness_delay=0,
        session=session,
    )

    pages = crawler.crawl(on_page_failed=lambda count, url, error: failures.append(url))

    assert [page.url for page in pages] == [
        "https://quotes.toscrape.com",
        "https://quotes.toscrape.com/page/2",
    ]
    assert crawler.failures[0].url == "https://quotes.toscrape.com/missing"
    assert failures == ["https://quotes.toscrape.com/missing"]


def test_crawler_skips_duplicate_content():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": '<a href="/copy/"></a><p>Same quote</p>',
            "https://quotes.toscrape.com/copy": "<p>Same quote</p>",
        }
    )

    crawler = Crawler(
        "https://quotes.toscrape.com/",
        politeness_delay=0,
        session=session,
    )

    pages = crawler.crawl()

    assert [page.url for page in pages] == ["https://quotes.toscrape.com"]


def test_duplicate_content_hash_skipped():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": '<a href="/copy-a/"></a><p>Same quote</p>',
            "https://quotes.toscrape.com/copy-a": '<a href="/copy-b/"></a><p>Same quote</p>',
            "https://quotes.toscrape.com/copy-b": "<p>Same quote</p>",
        }
    )
    progress_counts = []

    crawler = Crawler(
        "https://quotes.toscrape.com/",
        politeness_delay=0,
        session=session,
    )

    pages = crawler.crawl(on_page_crawled=lambda count, url: progress_counts.append(count))

    assert session.requested_urls == [
        "https://quotes.toscrape.com",
        "https://quotes.toscrape.com/copy-a",
        "https://quotes.toscrape.com/copy-b",
    ]
    assert [page.url for page in pages] == ["https://quotes.toscrape.com"]
    assert progress_counts == [1, 1, 1]

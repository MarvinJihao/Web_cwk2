from src.crawler import Crawler
from tests.helpers import FakeSession


def test_crawler_collects_internal_pages_and_text():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": """
                <html><body>
                  <title>Quotes</title>
                  <p>First quote</p>
                  <a href="/page/2/">next</a>
                  <a href="https://external.example/">external</a>
                </body></html>
            """,
            "https://quotes.toscrape.com/page/2": "<html><body>Second quote</body></html>",
        }
    )

    crawler = Crawler(
        "https://quotes.toscrape.com/",
        politeness_delay=0,
        session=session,
    )

    pages = crawler.crawl()

    assert [page.url for page in pages] == [
        "https://quotes.toscrape.com",
        "https://quotes.toscrape.com/page/2",
    ]
    assert "First quote" in pages[0].text
    assert "Second quote" in pages[1].text
    assert pages[0].title == "Quotes"
    assert pages[0].status == 200
    assert pages[0].content_hash


def test_crawler_waits_between_successive_requests():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": '<a href="/page/2/">next</a>',
            "https://quotes.toscrape.com/page/2": "Done",
        }
    )
    sleeps = []

    crawler = Crawler(
        "https://quotes.toscrape.com/",
        politeness_delay=6,
        session=session,
        sleeper=sleeps.append,
    )

    crawler.crawl()

    assert sleeps == [6]


def test_crawler_can_filter_internal_links():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": """
                <a href="/page/2/">next</a>
                <a href="/author/Albert-Einstein/">author</a>
            """,
            "https://quotes.toscrape.com/page/2": "Done",
        }
    )

    crawler = Crawler(
        "https://quotes.toscrape.com/",
        politeness_delay=0,
        session=session,
        url_filter=lambda url: "/author/" not in url,
    )

    pages = crawler.crawl()

    assert [page.url for page in pages] == [
        "https://quotes.toscrape.com",
        "https://quotes.toscrape.com/page/2",
    ]

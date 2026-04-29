from src.crawler import Crawler
from tests.helpers import FakeSession


def test_crawler_treats_page_one_as_homepage():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": """
                <html><body>
                  <p>First quote</p>
                  <a href="/page/1/">page one</a>
                </body></html>
            """,
        }
    )

    crawler = Crawler(
        "https://quotes.toscrape.com/",
        politeness_delay=0,
        session=session,
    )

    pages = crawler.crawl()

    assert [page.url for page in pages] == ["https://quotes.toscrape.com"]


def test_page_one_canonicalised_to_homepage():
    session = FakeSession(
        {
            "https://quotes.toscrape.com": """
                <a href="/page/1">page one without slash</a>
                <a href="/page/1/">page one with slash</a>
            """,
        }
    )

    crawler = Crawler(
        "https://quotes.toscrape.com/page/1/",
        politeness_delay=0,
        session=session,
    )

    pages = crawler.crawl()

    assert [page.url for page in pages] == ["https://quotes.toscrape.com"]
    assert session.requested_urls == ["https://quotes.toscrape.com"]

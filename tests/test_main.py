from src.main import SearchShell


def test_default_crawl_boundary_keeps_quote_listing_pages_only():
    assert SearchShell._should_crawl_url("https://quotes.toscrape.com")
    assert SearchShell._should_crawl_url("https://quotes.toscrape.com/")
    assert SearchShell._should_crawl_url("https://quotes.toscrape.com/page/2")

    assert not SearchShell._should_crawl_url("https://quotes.toscrape.com/author/Albert-Einstein")
    assert not SearchShell._should_crawl_url("https://quotes.toscrape.com/tag/life")
    assert not SearchShell._should_crawl_url("https://quotes.toscrape.com/login")

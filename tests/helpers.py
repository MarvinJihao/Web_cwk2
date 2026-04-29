class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, pages):
        self.pages = pages
        self.requested_urls = []

    def get(self, url, timeout):
        self.requested_urls.append(url)
        return FakeResponse(self.pages[url])

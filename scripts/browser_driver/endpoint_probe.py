import re
from urllib.parse import quote, urlsplit

from browser_driver.endpoint_probe_js import (
    READ_ENDPOINT_DETAIL,
    READ_METHOD_CODE,
    READ_SIDEBAR,
)


class EndpointProbe:
    def __init__(self, page) -> None:
        self._page = page

    def open_endpoint(self, slug: str, entry_id: str = "") -> None:
        row = self._page.locator(f'[data-testid="endpoint-{slug}"]')
        if entry_id and not (row.count() and row.first.is_visible()):
            origin = "{0.scheme}://{0.netloc}".format(urlsplit(self._page.url))
            self._page.goto(f"{origin}/endpoint-fixture?entry={quote(entry_id, safe='')}")
        else:
            row.first.click()
        self._page.wait_for_selector('[data-testid="endpoint-page"]', timeout=30000)
        self._page.wait_for_timeout(600)

    def detail(self) -> dict:
        return self._page.evaluate(READ_ENDPOINT_DETAIL)

    def open_method(self, fqn: str) -> None:
        testid = "key-method-" + re.sub(r"[^A-Za-z0-9]+", "_", fqn)
        self._page.click(f'[data-testid="{testid}"]')
        self._page.wait_for_selector('[data-testid="method-code"]', timeout=10000)
        self._page.wait_for_timeout(300)

    def method_code(self) -> dict:
        return self._page.evaluate(READ_METHOD_CODE)

    def method_back(self) -> None:
        self._page.click('[data-testid="method-back"]')
        self._page.wait_for_timeout(300)

    def open_diagram(self) -> None:
        self._page.click('[data-testid="view-diagram"]')
        self._page.wait_for_selector(".react-flow__node", timeout=30000)
        self._page.wait_for_timeout(600)

    def sidebar(self) -> dict:
        return self._page.evaluate(READ_SIDEBAR)

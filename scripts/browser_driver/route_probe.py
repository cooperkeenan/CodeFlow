from browser_driver.route_probe_js import READ_CARDS, READ_HAPPY, READ_SETTLED

_CARD = '[data-testid^="contract-card-"]'


class RouteProbe:
    def __init__(self, page) -> None:
        self._page = page

    def select_route(self, handler_fqn: str) -> None:
        cards = self._page.evaluate(READ_CARDS)
        index = next((c["index"] for c in cards if c["handler"] == handler_fqn), None)
        if index is None:
            raise RuntimeError(f"no contract card with data-handler={handler_fqn} ({len(cards)} cards on this page; use --home endpoint:<group id> first)")
        self._page.locator(_CARD).nth(index).click()
        self._page.wait_for_selector(".react-flow__node", timeout=30000)
        self._wait_settled()

    def happy(self) -> dict:
        return self._page.evaluate(READ_HAPPY)

    def _wait_settled(self) -> None:
        previous = None
        for _ in range(40):
            self._page.wait_for_timeout(250)
            current = self._page.evaluate(READ_SETTLED)
            if current == previous:
                return
            previous = current

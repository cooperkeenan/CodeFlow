import json
import re
from pathlib import Path

from browser_driver.route_probe_js import READ_CARDS, READ_HAPPY

_CARD = '[data-testid^="contract-card-"]'


class RouteProbe:
    def __init__(self, page, endpoint_dir: Path) -> None:
        self._page = page
        self._endpoint_dir = endpoint_dir

    def select_route(self, handler_fqn: str) -> str:
        cards = self._page.evaluate(READ_CARDS)
        index = next((c["index"] for c in cards if c["handler"] == handler_fqn), None)
        how = "data-handler"
        if index is None:
            index = self._member_index(handler_fqn)
            how = f"fallback member index {index} (no data-handler on cards)"
        if index is None or index >= len(cards):
            raise RuntimeError(f"no contract card for {handler_fqn} ({len(cards)} cards on this page; route: needs the endpoint overview page, use --home endpoint:<id>)")
        self._page.locator(_CARD).nth(index).click()
        self._page.wait_for_selector(".react-flow__node", timeout=30000)
        self._page.wait_for_timeout(900)
        return how

    def happy(self) -> dict:
        return self._page.evaluate(READ_HAPPY)

    def _member_index(self, handler_fqn: str) -> int | None:
        suffix = f"__{_slug(handler_fqn)}.json"
        match = next(self._endpoint_dir.glob(f"route_*{suffix}"), None)
        if match is None:
            return None
        prefix = match.name[: -len(suffix)]
        routes = []
        for path in self._endpoint_dir.glob(f"{prefix}__*.json"):
            route = json.loads(path.read_text(encoding="utf-8")).get("route") or {}
            routes.append((route["path"], route["method"], route["handler_fqn"]))
        handlers = [route[2] for route in sorted(routes)]
        return handlers.index(handler_fqn) if handler_fqn in handlers else None


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value)

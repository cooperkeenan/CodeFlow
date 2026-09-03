from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_driver.dev_server import DevServer
from browser_driver.flow_probe_js import READ_DIMMED, READ_FLOWCHART, READ_ISOLATED, READ_STATE


class FlowSession:
    def __init__(
        self,
        frontend_dir: Path,
        port: int,
        url: str,
        explain_payload: dict | None = None,
        repo: str | None = None,
    ) -> None:
        self._server = DevServer(frontend_dir, port)
        self._url = f"{url}?repo={repo}" if repo else url
        self._explain_payload = explain_payload
        self._started = False
        self._playwright = None
        self._browser = None
        self._page = None

    def __enter__(self) -> "FlowSession":
        self._started = self._server.ensure_running()
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True, channel="chrome")
        self._page = self._browser.new_page(viewport={"width": 2000, "height": 1400})
        if self._explain_payload is not None:
            self._page.route("**/explain", lambda route: route.fulfill(json=self._explain_payload))
        self._page.goto(self._url, wait_until="networkidle")
        self._page.wait_for_selector(".react-flow__node", timeout=30000)
        return self

    def __exit__(self, *_: object) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        if self._started:
            self._server.stop()

    def state(self) -> dict:
        return self._page.evaluate(READ_STATE)

    def toggle(self, node_id: str) -> None:
        selector = f'.react-flow__node[data-id="{node_id}"] [role="button"]:not([data-testid="isolate-button"])'
        self._page.click(selector)
        self._page.wait_for_timeout(350)

    def isolate(self, node_id: str) -> None:
        self._page.click(f'.react-flow__node[data-id="{node_id}"] [data-testid="isolate-button"]')
        self._page.wait_for_timeout(1300)

    def click_node(self, node_id: str) -> None:
        self._page.click(f'.react-flow__node[data-id="{node_id}"]')
        self._page.wait_for_timeout(250)

    def press_button(self, text: str) -> None:
        self._page.click(f'header button:has-text("{text}")')
        self._page.wait_for_timeout(350)

    def fit(self) -> None:
        self._page.eval_on_selector(".react-flow__controls-fitview", "el => el.click()")
        self._page.wait_for_timeout(500)

    def shot(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(path), full_page=False)

    def isolated(self) -> dict:
        return self._page.evaluate(READ_ISOLATED)

    def dimmed(self) -> dict:
        return self._page.evaluate(READ_DIMMED)

    def flowchart(self) -> dict:
        return self._page.evaluate(READ_FLOWCHART)

    def tap(self, testid: str) -> None:
        self._page.click(f'[data-testid="{testid}"]')
        self._page.wait_for_timeout(250)

    def pick_symbol(self, name: str) -> None:
        self._page.click(f'[data-method="{name}"], [data-helper="{name}"]')
        self._page.wait_for_timeout(300)

    def press_key(self, key: str) -> None:
        self._page.keyboard.press(key)
        self._page.wait_for_timeout(1300)

    def overlaps(self) -> list[tuple[str, str]]:
        nodes = [
            n
            for n in self.state()["nodes"]
            if n["x"] is not None and not (n["id"] or "").startswith("box:")
        ]
        found: list[tuple[str, str]] = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b = nodes[i], nodes[j]
                if (
                    a["x"] < b["x"] + b["w"]
                    and b["x"] < a["x"] + a["w"]
                    and a["y"] < b["y"] + b["h"]
                    and b["y"] < a["y"] + a["h"]
                ):
                    found.append((a["id"], b["id"]))
        return sorted(found)

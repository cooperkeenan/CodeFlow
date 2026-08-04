from pathlib import Path

from playwright.sync_api import sync_playwright

from dev_server import DevServer

_READ_STATE = """
() => {
  const parse = (el) => {
    const m = /translate\\(([-0-9.]+)px,\\s*([-0-9.]+)px\\)/.exec(el.style.transform || '');
    const btn = el.querySelector('[role="button"]');
    return {
      id: el.getAttribute('data-id'),
      x: m ? Math.round(parseFloat(m[1])) : null,
      y: m ? Math.round(parseFloat(m[2])) : null,
      w: el.offsetWidth,
      h: el.offsetHeight,
      label: (el.innerText || '').trim().split('\\n')[0],
      toggle: btn ? btn.innerText.trim() : null,
    };
  };
  return {
    nodes: [...document.querySelectorAll('.react-flow__node')].map(parse),
    edges: document.querySelectorAll('.react-flow__edge').length,
    header: (document.querySelector('header')?.innerText || '').replace(/\\n/g, ' | '),
  };
}
"""


class FlowSession:
    def __init__(self, frontend_dir: Path, port: int, url: str) -> None:
        self._server = DevServer(frontend_dir, port)
        self._url = url
        self._started = False
        self._playwright = None
        self._browser = None
        self._page = None

    def __enter__(self) -> "FlowSession":
        self._started = self._server.ensure_running()
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True, channel="chrome")
        self._page = self._browser.new_page(viewport={"width": 2000, "height": 1400})
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
        return self._page.evaluate(_READ_STATE)

    def toggle(self, node_id: str) -> None:
        self._page.click(f'.react-flow__node[data-id="{node_id}"] [role="button"]')
        self._page.wait_for_timeout(350)

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

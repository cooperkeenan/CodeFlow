import subprocess
import tempfile
from pathlib import Path

from dev_server import DevServer


class DevServerScreenshotter:
    def __init__(
        self,
        frontend_dir: Path,
        port: int,
        chrome_path: str,
        url: str,
        out_png: Path,
        window_size: str = "2000,1600",
        virtual_time_budget: str = "10000",
        start_timeout_s: float = 60.0,
    ) -> None:
        self._frontend_dir = frontend_dir
        self._port = port
        self._chrome_path = chrome_path
        self._url = url
        self._out_png = out_png
        self._window_size = window_size
        self._virtual_time_budget = virtual_time_budget
        self._start_timeout_s = start_timeout_s
        self._server = DevServer(frontend_dir, port, start_timeout_s)

    def run(self) -> None:
        started = self._server.ensure_running()
        try:
            self._take_screenshot()
        finally:
            if started:
                self._server.stop()

    def _take_screenshot(self) -> None:
        self._out_png.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="chrome-profile-") as profile_dir:
            cmd = [
                self._chrome_path,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--screenshot={self._out_png}",
                f"--window-size={self._window_size}",
                f"--virtual-time-budget={self._virtual_time_budget}",
                f"--user-data-dir={profile_dir}",
                self._url,
            ]
            proc = subprocess.Popen(cmd)
            try:
                proc.wait(timeout=45)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
                print("chrome did not exit cleanly; killed after screenshot timeout")

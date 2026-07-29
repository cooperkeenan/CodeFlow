import socket
import subprocess
import tempfile
import time
from pathlib import Path


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
        self._server_process: subprocess.Popen | None = None

    def run(self) -> None:
        started = self._ensure_server_running()
        try:
            self._take_screenshot()
        finally:
            if started:
                self._stop_server()

    def _port_open(self) -> bool:
        try:
            with socket.create_connection(("localhost", self._port), timeout=0.5):
                return True
        except OSError:
            return False

    def _ensure_server_running(self) -> bool:
        if self._port_open():
            print(f"dev server already running on :{self._port}")
            return False
        print(f"starting dev server on :{self._port}...")
        self._server_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(self._frontend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._wait_for_port()
        return True

    def _wait_for_port(self) -> None:
        deadline = time.monotonic() + self._start_timeout_s
        while time.monotonic() < deadline:
            if self._port_open():
                return
            time.sleep(0.5)
        self._stop_server()
        raise RuntimeError(
            f"dev server did not open port {self._port} within {self._start_timeout_s}s"
        )

    def _stop_server(self) -> None:
        if self._server_process is None:
            return
        self._server_process.terminate()
        try:
            self._server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._server_process.kill()
            self._server_process.wait(timeout=10)
        self._server_process = None

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

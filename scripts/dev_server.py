import socket
import subprocess
import time
from pathlib import Path


class DevServer:
    def __init__(self, frontend_dir: Path, port: int, start_timeout_s: float = 60.0) -> None:
        self._frontend_dir = frontend_dir
        self._port = port
        self._start_timeout_s = start_timeout_s
        self._process: subprocess.Popen | None = None

    def port_open(self) -> bool:
        try:
            with socket.create_connection(("localhost", self._port), timeout=0.5):
                return True
        except OSError:
            return False

    def ensure_running(self) -> bool:
        if self.port_open():
            print(f"dev server already running on :{self._port}")
            return False
        print(f"starting dev server on :{self._port}...")
        self._process = subprocess.Popen(
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
            if self.port_open():
                return
            time.sleep(0.5)
        self.stop()
        raise RuntimeError(
            f"dev server did not open port {self._port} within {self._start_timeout_s}s"
        )

    def stop(self) -> None:
        if self._process is None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=10)
        self._process = None

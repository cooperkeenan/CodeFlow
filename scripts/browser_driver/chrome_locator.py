import os
import shutil
import sys
from pathlib import Path

_MAC_PATHS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",)
_LINUX_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
_WINDOWS_SUBPATH = r"Google\Chrome\Application\chrome.exe"
_WINDOWS_ROOTS = ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")


class ChromeLocator:
    def find(self) -> str:
        override = os.environ.get("CHROME_PATH")
        if override:
            return override
        for candidate in self._candidates():
            if candidate and Path(candidate).exists():
                return candidate
        raise RuntimeError(
            "Chrome not found; set CHROME_PATH to the browser executable"
        )

    def _candidates(self) -> list[str]:
        if sys.platform == "darwin":
            return list(_MAC_PATHS)
        if sys.platform == "win32":
            roots = (os.environ.get(name) for name in _WINDOWS_ROOTS)
            return [str(Path(root) / _WINDOWS_SUBPATH) for root in roots if root]
        return [path for path in (shutil.which(n) for n in _LINUX_NAMES) if path]

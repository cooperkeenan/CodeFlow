import base64
import logging
import tempfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_API_URL = "https://api.github.com"
_EXCLUDED_FILES = {"__init__.py", "conftest.py"}
_EXCLUDED_DIRS = {"__pycache__", ".venv", "venv", "tests", "test"}


class FileFetchService:
    def __init__(self, http_client: httpx.AsyncClient):
        self._http = http_client

    async def fetch_files_to_temp(
        self,
        access_token: str,
        repo_name: str,
        directories: list[str],
    ) -> tuple[str, list[str]]:
        owner, repo = repo_name.split("/")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        temp_dir = tempfile.mkdtemp()
        written_files = []

        for directory in directories:
            logger.info("Fetching files in %s", directory)
            response = await self._http.get(
                f"{_API_URL}/repos/{owner}/{repo}/contents/{directory.rstrip('/')}",
                headers=headers,
            )
            if response.status_code != 200:
                logger.warning("Could not fetch directory %s", directory)
                continue

            for item in response.json():
                if item["type"] != "file":
                    continue
                if not item["name"].endswith(".py"):
                    continue
                if item["name"] in _EXCLUDED_FILES:
                    continue
                if any(ex in item["path"].split("/") for ex in _EXCLUDED_DIRS):
                    continue

                file_response = await self._http.get(item["url"], headers=headers)
                if file_response.status_code != 200:
                    continue

                content = base64.b64decode(
                    file_response.json()["content"]
                ).decode("utf-8")

                file_path = Path(temp_dir) / item["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                written_files.append(str(file_path))
                logger.info("Written %s", item["path"])

        return temp_dir, written_files
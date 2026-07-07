import base64
import logging
import shutil
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

    async def fetch_files(
        self,
        *,
        repo_name: str | None = None,
        access_token: str | None = None,
        local_path: str | None = None,
        directories: list[str],
    ) -> tuple[str, list[str]]:
        if local_path:
            return self._copy_local_files(local_path, directories)
        if not access_token or not repo_name:
            raise ValueError(
                "fetch_files requires local_path for local repos or "
                "both access_token and repo_name for GitHub repos"
            )
        return await self.fetch_files_to_temp(access_token, repo_name, directories)

    def _copy_local_files(
        self,
        local_path: str,
        directories: list[str],
    ) -> tuple[str, list[str]]:
        root = Path(local_path)
        temp_dir = tempfile.mkdtemp()
        written_files: list[str] = []
        for directory in directories:
            source_path = root / directory.rstrip("/")
            if not source_path.exists():
                logger.warning("Path not found: %s", source_path)
                continue
            candidates = [source_path] if source_path.is_file() else list(source_path.rglob("*.py"))
            for file_path in candidates:
                if not self._is_included(file_path):
                    continue
                dest = Path(temp_dir) / file_path.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest)
                written_files.append(str(dest))
                logger.info("Copied %s", file_path.name)
        return temp_dir, written_files

    def _is_included(self, file_path: Path) -> bool:
        if file_path.suffix != ".py":
            return False
        if file_path.name in _EXCLUDED_FILES:
            return False
        return not any(ex in file_path.parts for ex in _EXCLUDED_DIRS)

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

        tree_items = await self._get_recursive_tree(owner, repo, headers)
        matching_items = self._filter_items(tree_items, directories)

        temp_dir = tempfile.mkdtemp()
        written_files = []

        for item in matching_items:
            content = await self._fetch_blob(item["url"], headers)
            if content is None:
                continue
            file_path = Path(temp_dir) / item["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            written_files.append(str(file_path))
            logger.info("Written %s", item["path"])

        logger.info("Fetched %d files from GitHub", len(written_files))
        return temp_dir, written_files

    async def _get_recursive_tree(
        self, owner: str, repo: str, headers: dict
    ) -> list[dict]:
        for branch in ("main", "master"):
            response = await self._http.get(
                f"{_API_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                headers=headers,
            )
            if response.status_code == 200:
                return response.json().get("tree", [])
        logger.warning("Could not fetch git tree for %s/%s", owner, repo)
        return []

    def _filter_items(
        self, tree_items: list[dict], directories: list[str]
    ) -> list[dict]:
        norm_dirs = [d.rstrip("/") for d in directories]
        results = []
        for item in tree_items:
            if item["type"] != "blob":
                continue
            path = item["path"]
            if not path.endswith(".py"):
                continue
            parts = path.split("/")
            if parts[-1] in _EXCLUDED_FILES:
                continue
            if any(ex in parts for ex in _EXCLUDED_DIRS):
                continue
            if any(path == d or path.startswith(d + "/") for d in norm_dirs):
                results.append(item)
        return results

    async def _fetch_blob(self, url: str, headers: dict) -> str | None:
        response = await self._http.get(url, headers=headers)
        if response.status_code != 200:
            logger.warning("Could not fetch blob from %s", url)
            return None
        return base64.b64decode(response.json()["content"]).decode("utf-8")

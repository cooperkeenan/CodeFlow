import base64
import logging
import tempfile
from pathlib import Path

import httpx
from tracer.services.evidence.file_inclusion import EXCLUDED_DIRS, EXCLUDED_FILES

logger = logging.getLogger(__name__)

_API_URL = "https://api.github.com"


class GitHubFileFetcher:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
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
            if parts[-1] in EXCLUDED_FILES:
                continue
            if any(ex in parts for ex in EXCLUDED_DIRS):
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

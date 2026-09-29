import base64
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

EXCLUDED = {".git", ".github", "__pycache__", "node_modules", ".venv", "venv"}
MANIFEST_FILES = {
    "requirements.txt", "pyproject.toml", "package.json",
    "pom.xml", "build.gradle", "go.mod", "Cargo.toml",
    "docker-compose.yml", "docker-compose.yaml",
}
_API_URL = "https://api.github.com"


def _nested_repo_dirs(raw_paths: list[str]) -> set[str]:
    dirs = set()
    for path in raw_paths:
        parts = path.split("/")
        if ".git" in parts:
            idx = parts.index(".git")
            if idx > 0:
                dir_name = "/".join(parts[:idx])
                dirs.add(dir_name)
                logger.info("Excluding nested git repo directory: %s", dir_name)
    return dirs


def _within_any(path: str, dirs: set[str]) -> bool:
    return any(path == d or path.startswith(d + "/") for d in dirs)


class FileTreeService:
    def __init__(self, http_client: httpx.AsyncClient):
        self._http = http_client

    async def get_tree(
        self,
        *,
        repo_name: str | None = None,
        access_token: str | None = None,
        local_path: str | None = None,
    ) -> list[str]:
        logger.info("Fetching file tree")
        if local_path:
            raw_paths = self._local_tree(local_path)
        else:
            if access_token is None or repo_name is None:
                raise ValueError("access_token and repo_name required for GitHub tree")
            raw_paths = await self._github_tree(access_token, repo_name)
        nested_repos = _nested_repo_dirs(raw_paths)
        paths = [p for p in raw_paths if not any(ex in p.split("/") for ex in EXCLUDED)]
        result = [p for p in paths if not _within_any(p, nested_repos)]
        logger.info("Found %d files (%d nested repo dirs excluded)", len(result), len(nested_repos))
        return result

    def _local_tree(self, local_path: str) -> list[str]:
        root = Path(local_path)
        result = []
        for p in root.rglob("*"):
            if p.is_file() or (p.is_dir() and p.name == ".git"):
                result.append(p.relative_to(root).as_posix())
        return result

    async def _github_tree(self, access_token: str, repo_name: str) -> list[str]:
        owner, repo = repo_name.split("/")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = None
        for branch in ("main", "master"):
            response = await self._http.get(
                f"{_API_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                headers=headers,
            )
            if response.status_code == 200:
                break
        assert response is not None
        response.raise_for_status()
        return [
            item["path"]
            for item in response.json().get("tree", [])
            if item["type"] == "blob"
        ]

    async def get_manifests(
        self,
        *,
        repo_name: str | None = None,
        access_token: str | None = None,
        local_path: str | None = None,
        paths: list[str],
    ) -> dict[str, str]:
        logger.info("Fetching manifest files")
        if local_path:
            return self._local_manifests(local_path, paths)
        if access_token is None or repo_name is None:
            raise ValueError("access_token and repo_name required for GitHub manifests")
        return await self._github_manifests(access_token, repo_name, paths)

    def _local_manifests(self, local_path: str, paths: list[str]) -> dict[str, str]:
        root = Path(local_path)
        manifests = {}
        for path in paths:
            if Path(path).name in MANIFEST_FILES:
                full_path = root / path
                if full_path.exists():
                    manifests[path] = full_path.read_text(encoding="utf-8")
                    logger.info("Read manifest: %s", path)
        return manifests

    async def _github_manifests(
        self, access_token: str, repo_name: str, paths: list[str]
    ) -> dict[str, str]:
        owner, repo = repo_name.split("/")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        manifests = {}
        for path in paths:
            if path.split("/")[-1] not in MANIFEST_FILES:
                continue
            response = await self._http.get(
                f"{_API_URL}/repos/{owner}/{repo}/contents/{path}",
                headers=headers,
            )
            if response.status_code == 200:
                content = base64.b64decode(response.json()["content"]).decode("utf-8")
                manifests[path] = content
                logger.info("Retrieved manifest: %s", path)
        return manifests

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

_EMBED_MANIFESTS = frozenset({"requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml"})
_EMBED_DEPLOY = frozenset({"Dockerfile", "docker-compose.yml", "docker-compose.yaml"})


def _embedded_repo_dirs(paths: list[str]) -> set[str]:
    by_dir: dict[str, set[str]] = {}
    for path in paths:
        parts = path.split("/")
        if len(parts) > 1:
            top, filename = parts[0], parts[-1]
            by_dir.setdefault(top, set()).add(filename)
    embedded = set()
    for dir_name, filenames in by_dir.items():
        if filenames & _EMBED_MANIFESTS and filenames & _EMBED_DEPLOY:
            embedded.add(dir_name)
            logger.info("Excluding embedded repo directory: %s", dir_name)
    return embedded


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
        paths = [p for p in raw_paths if not any(ex in p.split("/") for ex in EXCLUDED)]
        embedded = _embedded_repo_dirs(paths)
        result = [p for p in paths if not embedded or p.split("/")[0] not in embedded]
        logger.info("Found %d files (%d embedded dirs excluded)", len(result), len(embedded))
        return result

    def _local_tree(self, local_path: str) -> list[str]:
        root = Path(local_path)
        return [
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file()
        ]

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

import base64
import logging

import httpx

logger = logging.getLogger(__name__)

EXCLUDED = {".git", ".github", "__pycache__", "node_modules", ".venv", "venv"}
MANIFEST_FILES = {
    "requirements.txt", "pyproject.toml", "package.json",
    "pom.xml", "build.gradle", "go.mod", "Cargo.toml",
    "docker-compose.yml", "docker-compose.yaml",
}
_API_URL = "https://api.github.com"


class FileTreeService:
    def __init__(self, http_client: httpx.AsyncClient):
        self._http = http_client

    async def get_tree(self, access_token: str, repo_name: str) -> list[str]:
        logger.info("Fetching file tree for %s", repo_name)
        owner, repo = repo_name.split("/")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        for branch in ("main", "master"):
            response = await self._http.get(
                f"{_API_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                headers=headers,
            )
            if response.status_code == 200:
                break

        response.raise_for_status()
        paths = [
            item["path"] for item in response.json().get("tree", [])
            if item["type"] == "blob"
            and not any(ex in item["path"].split("/") for ex in EXCLUDED)
        ]
        logger.info("Found %d files in %s", len(paths), repo_name)
        return paths

    async def get_manifest_files(self, access_token: str, repo_name: str, paths: list[str]) -> dict[str, str]:
        logger.info("Fetching manifest files for %s", repo_name)
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
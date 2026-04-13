import json
import logging
from pathlib import Path

from services.file_tree_service import FileTreeService

logger = logging.getLogger(__name__)

MANIFEST_FILES = {
    "requirements.txt", "pyproject.toml", "package.json",
    "pom.xml", "build.gradle", "go.mod", "Cargo.toml",
    "docker-compose.yml", "docker-compose.yaml",
}

GET_MANIFEST_FILES_SCHEMA = {
    "name": "get_manifest_files",
    "description": (
        "Fetch the contents of dependency and config files. "
        "Pass either a local_path for local repos or access_token and repo_name for GitHub."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "GitHub OAuth access token"},
            "repo_name": {"type": "string", "description": "Full repo name e.g. owner/repo"},
            "local_path": {"type": "string", "description": "Absolute path to local repo"},
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths from get_file_tree",
            },
        },
        "required": ["paths"],
    },
}


class GetManifestFilesTool:
    def __init__(self, service: FileTreeService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("Getting manifest files")
        try:
            if tool_input.get("local_path"):
                result = self._get_local_manifests(
                    tool_input["local_path"],
                    tool_input["paths"],
                )
            else:
                result = await self._service.get_manifest_files(
                    tool_input["access_token"],
                    tool_input["repo_name"],
                    tool_input["paths"],
                )
            return json.dumps(result)
        except Exception as e:
            logger.error("get_manifest_files failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})

    def _get_local_manifests(self, local_path: str, paths: list[str]) -> dict[str, str]:
        root = Path(local_path)
        manifests = {}
        for path in paths:
            if Path(path).name in MANIFEST_FILES:
                full_path = root / path
                if full_path.exists():
                    manifests[path] = full_path.read_text(encoding="utf-8")
                    logger.info("Read manifest: %s", path)
        return manifests
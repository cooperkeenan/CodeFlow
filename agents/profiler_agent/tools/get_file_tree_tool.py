import json
import logging
from pathlib import Path

from services.file_tree_service import FileTreeService

logger = logging.getLogger(__name__)

GET_FILE_TREE_SCHEMA = {
    "name": "get_file_tree",
    "description": (
        "Fetch the full file path list for a repository. "
        "Pass either a local_path for local repos or access_token and repo_name for GitHub."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "GitHub OAuth access token"},
            "repo_name": {"type": "string", "description": "Full repo name e.g. owner/repo"},
            "local_path": {"type": "string", "description": "Absolute path to local repo"},
        },
    },
}


class GetFileTreeTool:
    def __init__(self, service: FileTreeService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("Getting file tree")
        try:
            if tool_input.get("local_path"):
                result = self._get_local_tree(tool_input["local_path"])
            else:
                result = await self._service.get_tree(
                    tool_input["access_token"],
                    tool_input["repo_name"],
                )
            return json.dumps(result)
        except Exception as e:
            logger.error("get_file_tree failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})

    def _get_local_tree(self, local_path: str) -> list[str]:
        root = Path(local_path)
        excluded = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        excluded |= self._embedded_repo_dirs(root)
        paths = []
        for path in root.rglob("*"):
            if path.is_file() and not any(ex in path.parts for ex in excluded):
                paths.append(str(path.relative_to(root)))
        logger.info("Found %d files in local path", len(paths))
        return paths

    def _embedded_repo_dirs(self, root: Path) -> set[str]:
        _manifests = {"requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml"}
        _deploy = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
        embedded = set()
        for d in root.iterdir():
            if not d.is_dir():
                continue
            if any((d / m).exists() for m in _manifests) and any((d / m).exists() for m in _deploy):
                embedded.add(d.name)
                logger.info("Excluding embedded repo directory: %s", d.name)
        return embedded
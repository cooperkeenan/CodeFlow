import json
import logging
import shutil
import tempfile
from pathlib import Path

from services.file_fetch_service import FileFetchService  # type: ignore

logger = logging.getLogger(__name__)

FETCH_LAYER_FILES_SCHEMA = {
    "name": "fetch_layer_files",
    "description": (
        "Fetch source files from specific directories. "
        "Pass local_path for local repos or access_token and repo_name for GitHub. "
        "Returns temp_dir and file_paths for use with build_call_graph."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "GitHub OAuth access token"},
            "repo_name": {"type": "string", "description": "Full repo name e.g. owner/repo"},
            "local_path": {"type": "string", "description": "Absolute path to local repo"},
            "directories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of directory paths from layer_hints",
            },
        },
        "required": ["directories"],
    },
}


class FetchLayerFilesTool:
    def __init__(self, service: FileFetchService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("Fetching layer files: %s", tool_input["directories"])
        try:
            if tool_input.get("local_path"):
                temp_dir, file_paths = self._copy_local_files(
                    tool_input["local_path"],
                    tool_input["directories"],
                )
            else:
                if not tool_input.get("access_token") or not tool_input.get("repo_name"):
                    raise ValueError(
                        "fetch_layer_files requires local_path for local repos or "
                        "both access_token and repo_name for GitHub repos"
                    )
                temp_dir, file_paths = await self._service.fetch_files_to_temp(
                    tool_input["access_token"],
                    tool_input["repo_name"],
                    tool_input["directories"],
                )
            return json.dumps({"temp_dir": temp_dir, "file_paths": file_paths})
        except Exception as e:
            logger.error("fetch_layer_files failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})

    def _copy_local_files(
        self,
        local_path: str,
        directories: list[str],
    ) -> tuple[str, list[str]]:
        root = Path(local_path)
        temp_dir = tempfile.mkdtemp()
        written_files = []
        excluded = {"__pycache__", ".venv", "venv", "tests", "test"}

        for directory in directories:
            source_path = root / directory.rstrip("/")
            if not source_path.exists():
                logger.warning("Path not found: %s", source_path)
                continue

            if source_path.is_file():
                if source_path.suffix != ".py" or any(ex in source_path.parts for ex in excluded):
                    continue
                dest = Path(temp_dir) / source_path.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest)
                written_files.append(str(dest))
                logger.info("Copied %s", source_path.name)
                continue

            for file_path in source_path.rglob("*.py"):
                if any(ex in file_path.parts for ex in excluded):
                    continue
                dest = Path(temp_dir) / file_path.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest)
                written_files.append(str(dest))
                logger.info("Copied %s", file_path.name)

        return temp_dir, written_files

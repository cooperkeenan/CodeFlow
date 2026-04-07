import json
import logging

from services.file_tree_service import FileTreeService

logger = logging.getLogger(__name__)

GET_MANIFEST_FILES_SCHEMA = {
    "name": "get_manifest_files",
    "description": (
        "Fetch the contents of dependency and config files (requirements.txt, package.json etc). "
        "Use this after get_file_tree to identify frameworks and libraries."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "GitHub OAuth access token"},
            "repo_name": {"type": "string", "description": "Full repo name e.g. owner/repo"},
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths returned from get_file_tree",
            },
        },
        "required": ["access_token", "repo_name", "paths"],
    },
}


class GetManifestFilesTool:
    def __init__(self, service: FileTreeService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("Getting manifest files for %s", tool_input["repo_name"])
        try:
            result = await self._service.get_manifest_files(
                tool_input["access_token"],
                tool_input["repo_name"],
                tool_input["paths"],
            )
            return json.dumps(result)
        except Exception as e:
            logger.error("get_manifest_files failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})
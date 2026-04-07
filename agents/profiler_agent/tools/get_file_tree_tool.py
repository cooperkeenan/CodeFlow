import json
import logging

from services.file_tree_service import FileTreeService

logger = logging.getLogger(__name__)

GET_FILE_TREE_SCHEMA = {
    "name": "get_file_tree",
    "description": (
        "Fetch the full file path list for a GitHub repository. "
        "Use this first to understand the folder structure and identify architecture patterns."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "GitHub OAuth access token"},
            "repo_name": {"type": "string", "description": "Full repo name e.g. owner/repo"},
        },
        "required": ["access_token", "repo_name"],
    },
}


class GetFileTreeTool:
    def __init__(self, service: FileTreeService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("Getting file tree for %s", tool_input["repo_name"])
        try:
            result = await self._service.get_tree(
                tool_input["access_token"],
                tool_input["repo_name"],
            )
            return json.dumps(result)
        except Exception as e:
            logger.error("get_file_tree failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})
import json
import logging

from services.ast_service import AstService

logger = logging.getLogger(__name__)

PARSE_AST_SCHEMA = {
    "name": "parse_ast",
    "description": (
        "Parse the AST of source files to extract imports, classes, functions and calls. "
        "Pass the file contents returned by fetch_layer_files directly."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "files": {
                "type": "object",
                "description": "Dictionary of filepath to file content strings",
            },
        },
        "required": ["files"],
    },
}


class ParseAstTool:
    def __init__(self, service: AstService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("parse_ast tool_input keys: %s", list(tool_input.keys()))
        logger.info("parse_ast tool_input: %s", tool_input)
        try:
            results = [
                self._service.parse_file(filepath, content)
                for filepath, content in tool_input["files"].items()
            ]
            return json.dumps(results)
        except Exception as e:
            logger.error("parse_ast failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})
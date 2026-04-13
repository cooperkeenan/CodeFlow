import json
import logging

from services.call_graph_service import CallGraphService

logger = logging.getLogger(__name__)

BUILD_CALL_GRAPH_SCHEMA = {
    "name": "build_call_graph",
    "description": (
        "Build a call graph using pycg static analysis from files previously fetched. "
        "Pass the temp_dir and file_paths returned by fetch_layer_files. "
        "Returns nodes and edges showing which functions call which."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "temp_dir": {
                "type": "string",
                "description": "Temp directory path returned by fetch_layer_files",
            },
            "file_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths returned by fetch_layer_files",
            },
        },
        "required": ["temp_dir", "file_paths"],
    },
}


class BuildCallGraphTool:
    def __init__(self, service: CallGraphService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("Building call graph")
        try:
            result = self._service.build(
                tool_input["temp_dir"],
                tool_input["file_paths"],
            )
            return json.dumps(result)
        except Exception as e:
            logger.error("build_call_graph failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})
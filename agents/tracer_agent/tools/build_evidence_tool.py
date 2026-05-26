import json
import logging

from services.evidence_service import EvidenceService

logger = logging.getLogger(__name__)

BUILD_EVIDENCE_SCHEMA = {
    "name": "build_evidence",
    "description": (
        "Build an evidence bundle from fetched files and call graph. "
        "Pass temp_dir and file_paths from fetch_layer_files and call_graph from build_call_graph. "
        "Returns signatures, import_edges, call_edges, and confirmed_edges."
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
            "call_graph": {
                "type": "object",
                "description": "Call graph object returned by build_call_graph",
            },
        },
        "required": ["temp_dir", "file_paths", "call_graph"],
    },
}


class BuildEvidenceTool:
    def __init__(self, service: EvidenceService):
        self._service = service

    async def handle(self, tool_input: dict) -> str:
        logger.info("Building evidence bundle")
        try:
            result = self._service.build(
                tool_input["file_paths"],
                tool_input["call_graph"],
                tool_input["temp_dir"],
            )
            return json.dumps(result)
        except Exception as e:
            logger.error("build_evidence failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})

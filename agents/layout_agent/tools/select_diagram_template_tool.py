import json
import logging

from services.template_selector_service import SelectionResult, TemplateSelectorService
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramType

logger = logging.getLogger(__name__)

SELECT_DIAGRAM_TEMPLATE_SCHEMA = {
    "name": "select_diagram_template",
    "description": (
        "Validate and build a DiagramTemplate for the given type against the current spec. "
        "Returns the serialized template on success, or a structured rejection with a "
        "suggested alternative type when the spec exceeds the type's limits."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "diagram_type": {
                "type": "string",
                "enum": [
                    "pipeline",
                    "hub_and_spoke",
                    "layered_tier",
                    "hierarchy",
                    "mesh",
                    "dependency_graph",
                ],
                "description": "The diagram type to validate and build a template for.",
            }
        },
        "required": ["diagram_type"],
    },
}


class SelectDiagramTemplateTool:
    def __init__(self, service: TemplateSelectorService) -> None:
        self._service = service
        self._spec: DiagramSpec | None = None

    def bind_spec(self, spec: DiagramSpec) -> None:
        self._spec = spec

    async def handle(self, tool_input: dict) -> str:
        if self._spec is None:
            logger.error("select_diagram_template called before spec was bound")
            return json.dumps({"error": "spec not bound"})
        diagram_type: DiagramType = tool_input["diagram_type"]
        try:
            result: SelectionResult = self._service.select(diagram_type, self._spec)
            if result.ok and result.template is not None:
                return result.template.model_dump_json()
            return json.dumps(
                {
                    "ok": False,
                    "limit_hit": result.limit_hit,
                    "actual_count": result.actual_count,
                    "suggested_type": result.suggested_type,
                }
            )
        except Exception as e:
            logger.error("select_diagram_template failed: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})

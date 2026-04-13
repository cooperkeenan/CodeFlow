import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "shared" / "templates"

GET_DIAGRAM_TEMPLATE_SCHEMA = {
    "name": "get_diagram_template",
    "description": (
        "Fetch the diagram template for a given architecture type. "
        "Returns the zones, edge types, and schema to populate."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "architecture_type": {
                "type": "string",
                "description": "Architecture type: three-tier|microservices|spa|monolith|library",
            }
        },
        "required": ["architecture_type"],
    },
}


class GetDiagramTemplateTool:
    async def handle(self, tool_input: dict) -> str:
        architecture_type = tool_input["architecture_type"]
        logger.info("Loading template for %s", architecture_type)
        template_path = _TEMPLATES_DIR / f"{architecture_type}.json"
        if not template_path.exists():
            logger.warning("No template for %s, falling back to three-tier", architecture_type)
            template_path = _TEMPLATES_DIR / "three-tier.json"
        return template_path.read_text(encoding="utf-8")
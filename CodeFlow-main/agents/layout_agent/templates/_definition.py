from dataclasses import dataclass

from shared.models.diagram_template import DiagramType


@dataclass(frozen=True)
class TemplateDefinition:
    type: DiagramType
    node_limit: int
    max_depth: int | None
    required_meta: tuple[str, ...]
    optional_meta: tuple[str, ...]
    description: str

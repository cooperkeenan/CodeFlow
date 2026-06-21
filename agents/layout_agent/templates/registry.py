from core.template_config import TemplateLimitsConfig
from shared.models.diagram_template import DiagramType
from templates._definition import TemplateDefinition
from templates.dependency_graph import make_dependency_graph_definition
from templates.hierarchy import make_hierarchy_definition
from templates.hub_and_spoke import make_hub_and_spoke_definition
from templates.layered_tier import make_layered_tier_definition
from templates.mesh import make_mesh_definition
from templates.pipeline import make_pipeline_definition
from templates.relationship import make_relationship_definition

_CANONICAL_ORDER: list[DiagramType] = [
    "pipeline",
    "hub_and_spoke",
    "layered_tier",
    "hierarchy",
    "mesh",
    "dependency_graph",
    "relationship",
]


class TemplateRegistry:
    def __init__(self, config: TemplateLimitsConfig) -> None:
        self._defs: dict[DiagramType, TemplateDefinition] = {
            "pipeline": make_pipeline_definition(config),
            "hub_and_spoke": make_hub_and_spoke_definition(config),
            "layered_tier": make_layered_tier_definition(config),
            "hierarchy": make_hierarchy_definition(config),
            "mesh": make_mesh_definition(config),
            "dependency_graph": make_dependency_graph_definition(config),
            "relationship": make_relationship_definition(),
        }

    def get(self, diagram_type: DiagramType) -> TemplateDefinition:
        return self._defs[diagram_type]

    def descriptions(self) -> list[tuple[DiagramType, str, int]]:
        return [
            (t, self._defs[t].description, self._defs[t].node_limit)
            for t in _CANONICAL_ORDER
        ]

    def types(self) -> list[DiagramType]:
        return list(_CANONICAL_ORDER)

from core.template_config import TemplateLimitsConfig
from templates._definition import TemplateDefinition


def make_mesh_definition(config: TemplateLimitsConfig) -> TemplateDefinition:
    return TemplateDefinition(
        type="mesh",
        node_limit=config.mesh,
        max_depth=None,
        required_meta=(),
        optional_meta=(),
        description=(
            "Fallback layout for systems with many cross-cutting connections, bidirectional cycles, "
            "or no dominant structural pattern. Use only when pipeline, hub_and_spoke, layered_tier, "
            "hierarchy, and dependency_graph all fail to capture the shape of the edges. Nodes are "
            "placed freely with no imposed directionality."
        ),
    )

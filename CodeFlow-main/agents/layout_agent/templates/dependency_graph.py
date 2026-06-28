from core.template_config import TemplateLimitsConfig
from templates._definition import TemplateDefinition


def make_dependency_graph_definition(config: TemplateLimitsConfig) -> TemplateDefinition:
    return TemplateDefinition(
        type="dependency_graph",
        node_limit=config.dependency_graph,
        max_depth=None,
        required_meta=(),
        optional_meta=(),
        description=(
            "Directed edges showing which module depends on or calls which, without imposing a "
            "strict sequential or layered layout. Use when edges run in multiple directions, no "
            "single module dominates the graph as a hub, and the primary insight is the actual "
            "dependency structure: which modules rely on shared libraries, how services are wired "
            "together, or which components import from which. Prefer over hub_and_spoke when "
            "spokes also talk to each other, and over pipeline when the flow is not strictly "
            "sequential or has branches."
        ),
    )

from core.template_config import TemplateLimitsConfig
from templates._definition import TemplateDefinition


def make_hub_and_spoke_definition(config: TemplateLimitsConfig) -> TemplateDefinition:
    return TemplateDefinition(
        type="hub_and_spoke",
        node_limit=config.hub_and_spoke,
        max_depth=None,
        required_meta=("hub_id",),
        optional_meta=(),
        description=(
            "One central module connects to all others while the outer modules rarely or never "
            "connect directly to each other. The hub is the single coordination point — a router, "
            "orchestrator, shared dependency, or dispatcher that every other module calls into. "
            "Use when one module has a significantly higher in-degree or out-degree than the rest "
            "and the spokes have few or no edges between themselves. Avoid if two or more spokes "
            "also talk directly to each other — that edge pattern suits dependency_graph instead."
        ),
    )

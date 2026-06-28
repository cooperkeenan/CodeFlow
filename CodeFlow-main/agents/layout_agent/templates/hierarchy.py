from core.template_config import TemplateLimitsConfig
from templates._definition import TemplateDefinition


def make_hierarchy_definition(config: TemplateLimitsConfig) -> TemplateDefinition:
    return TemplateDefinition(
        type="hierarchy",
        node_limit=config.hierarchy,
        max_depth=config.hierarchy_max_depth,
        required_meta=("parent_map", "depth_map"),
        optional_meta=(),
        description=(
            "Tree-shaped ownership where a root module delegates to child modules that may further "
            "delegate to their own children. Use when one module logically owns or contains others "
            "and the edge graph is acyclic with a clear root: a domain broken into sub-domains, a "
            "service broken into sub-services, a coordinator that spawns workers, or any system "
            "where the primary relationship is containment or delegation rather than sequential "
            "flow. Prefer over pipeline when the fan-out is vertical (one-to-many at each level) "
            "rather than linear."
        ),
    )

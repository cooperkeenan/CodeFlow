from core.template_config import TemplateLimitsConfig
from templates._definition import TemplateDefinition


def make_layered_tier_definition(config: TemplateLimitsConfig) -> TemplateDefinition:
    return TemplateDefinition(
        type="layered_tier",
        node_limit=config.layered_tier,
        max_depth=None,
        required_meta=("tier_indices",),
        optional_meta=(),
        description=(
            "Modules grouped into horizontal responsibility bands where traffic only crosses layer "
            "boundaries in one direction — upper layers call down, lower layers do not call up. "
            "Use when modules naturally cluster by their technical role rather than by sequential "
            "stage: for example intake / processing / storage, frontend / backend / database, or "
            "any stack where the roles form distinct tiers. Prefer over pipeline when multiple "
            "modules share the same tier and over hierarchy when the grouping is by technical "
            "responsibility rather than ownership."
        ),
    )

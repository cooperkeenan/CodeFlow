from core.template_config import TemplateLimitsConfig
from templates._definition import TemplateDefinition


def make_pipeline_definition(config: TemplateLimitsConfig) -> TemplateDefinition:
    return TemplateDefinition(
        type="pipeline",
        node_limit=config.pipeline,
        max_depth=None,
        required_meta=("module_order",),
        optional_meta=(),
        description=(
            "Modules arranged in a strict left-to-right sequence where data or control passes "
            "through each stage in order. Every module has at most one upstream producer and one "
            "downstream consumer — A completes before B begins. Use when the system reads as a "
            "chain: intake → analysis → transformation → output, or profiling → tracing → layout "
            "→ rendering, or any phased workflow where stage order is fixed and non-negotiable. "
            "Not restricted to build or deployment systems — any sequential processing chain qualifies."
        ),
    )

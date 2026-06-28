from templates._definition import TemplateDefinition


def make_relationship_definition() -> TemplateDefinition:
    return TemplateDefinition(
        type="relationship",
        node_limit=20,
        max_depth=None,
        required_meta=("focus",),
        optional_meta=("callers", "callees", "children"),
        description="Caller/callee neighborhood of a single component; fallback for mixed local graphs.",
    )

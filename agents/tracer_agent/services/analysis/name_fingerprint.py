import hashlib

from models.node_name_context import NodeNameContext
from prompts.flow_name_prompt import PROMPT_VERSION

_SEPARATOR = "\x1f"


def compute_fingerprint(context: NodeNameContext) -> str:
    node = context.node
    parts = [
        PROMPT_VERSION,
        node.kind,
        node.label,
        *sorted(node.backing),
        *context.arm_label_sources,
        node.effect_kind or "",
        node.effect_target or "",
        *sorted(context.child_labels),
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()

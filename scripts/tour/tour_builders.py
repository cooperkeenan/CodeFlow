from typing import Sequence

from shared.models.flow_graph import Badge, EffectKind, FlowNode, SourceRef

REPO_URL = "https://github.com/cooperkeenan/CodeFlow/blob/main"


def ref(file: str, line: int, end_line: int | None = None) -> SourceRef:
    return SourceRef(file=file, line=line, end_line=end_line or line)


def node(
    node_id: str,
    kind: str,
    lane: str,
    label: str,
    one_liner: str = "",
    refs: Sequence[SourceRef] = (),
    level: int = 0,
    container: str = "",
    children: Sequence[str] = (),
    body_kind: str = "list",
    body_head: str = "",
    body_tails: Sequence[str] = (),
    backing: Sequence[str] = (),
    effect_kind: EffectKind | None = None,
    effect_target: str = "",
    badges: Sequence[Badge] = (),
) -> FlowNode:
    return FlowNode(
        id=node_id,
        kind=kind,
        lane=lane,
        label=label,
        one_liner=one_liner,
        refs=list(refs),
        level=level,
        containers=[container] if container else [],
        hidden_children=list(children),
        body_kind=body_kind,
        body_head=body_head,
        body_tails=list(body_tails),
        backing=list(backing),
        effect_kind=effect_kind,
        effect_target=effect_target,
        badges=list(badges),
    )

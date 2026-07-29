from dataclasses import dataclass, field

from shared.models.flow_graph import Badge, EdgeKind, EffectKind, FlowEdge, FlowNode, NodeKind, SourceRef


@dataclass
class _NodeDraft:
    id: str
    kind: NodeKind
    lane: str
    label: str
    backing: list[str] = field(default_factory=list)
    refs: list[SourceRef] = field(default_factory=list)
    badges: set[Badge] = field(default_factory=set)
    effect_kind: EffectKind | None = None
    effect_target: str = ""
    folded_count: int = 0


@dataclass
class _EdgeDraft:
    source: str
    target: str
    kind: EdgeKind
    arm_label: str = ""
    group_id: str = ""
    confidence: str = "resolved"


class GraphAccumulator:
    def __init__(self) -> None:
        self._nodes: dict[str, _NodeDraft] = {}
        self._edges: dict[tuple[str, str, str], _EdgeDraft] = {}

    def upsert(
        self,
        node_id: str,
        kind: NodeKind,
        lane: str,
        label: str,
        backing: list[str] | None = None,
        refs: list[SourceRef] | None = None,
        badges: set[Badge] | None = None,
        effect_kind: EffectKind | None = None,
        effect_target: str = "",
        folded_count: int = 0,
    ) -> str:
        draft = self._nodes.get(node_id)
        if draft is None:
            draft = _NodeDraft(id=node_id, kind=kind, lane=lane, label=label)
            self._nodes[node_id] = draft
        if folded_count:
            draft.folded_count = folded_count
        for fqn in backing or []:
            if fqn not in draft.backing:
                draft.backing.append(fqn)
        for ref in refs or []:
            if ref not in draft.refs:
                draft.refs.append(ref)
        draft.badges.update(badges or set())
        if effect_kind is not None:
            draft.effect_kind = effect_kind
        if effect_target:
            draft.effect_target = effect_target
        return node_id

    def add_badge(self, node_id: str, badge: Badge) -> None:
        draft = self._nodes.get(node_id)
        if draft is not None:
            draft.badges.add(badge)

    def connect(
        self,
        source: str,
        target: str,
        kind: EdgeKind,
        arm_label: str = "",
        group_id: str = "",
        confidence: str = "resolved",
    ) -> None:
        if source == target:
            return
        key = (source, target, arm_label)
        if key not in self._edges:
            self._edges[key] = _EdgeDraft(source, target, kind, arm_label, group_id, confidence)

    def nodes(self) -> dict[str, _NodeDraft]:
        return self._nodes

    def edges(self) -> dict[tuple[str, str, str], _EdgeDraft]:
        return self._edges

    def to_flow_nodes(self) -> list[FlowNode]:
        return [
            FlowNode(
                id=d.id,
                kind=d.kind,
                lane=d.lane,
                label=d.label,
                backing=list(d.backing),
                refs=list(d.refs),
                badges=sorted(d.badges),
                effect_kind=d.effect_kind,
                effect_target=d.effect_target,
                folded_count=d.folded_count,
            )
            for d in self._nodes.values()
        ]

    def to_flow_edges(self) -> list[FlowEdge]:
        return [
            FlowEdge(
                source=e.source,
                target=e.target,
                kind=e.kind,
                arm_label=e.arm_label,
                group_id=e.group_id,
                confidence=e.confidence,
            )
            for e in self._edges.values()
        ]

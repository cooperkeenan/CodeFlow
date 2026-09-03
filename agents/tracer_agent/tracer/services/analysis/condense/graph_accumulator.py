from tracer.services.analysis.condense.drafts import _EdgeDraft, _NodeDraft
from tracer.services.analysis.graph_ops import is_descendant

from shared.models.flow_graph import (
    Badge,
    EdgeKind,
    EffectKind,
    FlowEdge,
    FlowNode,
    NodeKind,
    SourceRef,
)


class GraphAccumulator:
    def __init__(self) -> None:
        self._nodes: dict[str, _NodeDraft] = {}
        self._edges: dict[tuple[str, str, str], _EdgeDraft] = {}
        self._call_boundaries: list[tuple[str, str, str]] = []
        self._effect_boundaries: list[tuple[str, str, str]] = []

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

    def set_owner(self, node_id: str, owner_fqn: str, arm_path: list[str]) -> None:
        draft = self._nodes.get(node_id)
        if draft is None or draft.owner_fqn:
            return
        draft.owner_fqn = owner_fqn
        draft.arm_path = list(arm_path)

    def add_container(self, node_id: str, container: str) -> None:
        draft = self._nodes.get(node_id)
        if draft is None or node_id == container:
            return
        if container in draft.containers:
            return
        if is_descendant(self._nodes, container, node_id):
            return
        draft.containers.append(container)

    def record_call_boundary(self, caller_fqn: str, local_container: str, callee_fqn: str) -> None:
        entry = (caller_fqn, local_container, callee_fqn)
        if entry not in self._call_boundaries:
            self._call_boundaries.append(entry)

    def call_boundaries(self) -> list[tuple[str, str, str]]:
        return self._call_boundaries

    def record_effect_boundary(self, caller_fqn: str, local_container: str, effect_id: str) -> None:
        entry = (caller_fqn, local_container, effect_id)
        if entry not in self._effect_boundaries:
            self._effect_boundaries.append(entry)

    def effect_boundaries(self) -> list[tuple[str, str, str]]:
        return self._effect_boundaries

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

    def remove_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        for key in [k for k, e in self._edges.items() if e.source == node_id or e.target == node_id]:
            del self._edges[key]

    def backing_index(self) -> dict[str, str]:
        index: dict[str, str] = {}
        for draft in self._nodes.values():
            for fqn in draft.backing:
                index.setdefault(fqn, draft.id)
        return index

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
                owner_fqn=d.owner_fqn,
                arm_path=list(d.arm_path),
                containers=sorted(d.containers),
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

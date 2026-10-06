from tracer.services.analysis.condense.drafts import _EdgeDraft, _NodeDraft

from shared.models.flow_graph import FlowEdge, FlowNode


class DraftExporter:
    def nodes(self, drafts: list[_NodeDraft]) -> list[FlowNode]:
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
                members=list(d.members),
                owner_fqn=d.owner_fqn,
                arm_path=list(d.arm_path),
                containers=sorted(d.containers),
            )
            for d in drafts
        ]

    def edges(self, drafts: list[_EdgeDraft]) -> list[FlowEdge]:
        return [
            FlowEdge(
                source=e.source,
                target=e.target,
                kind=e.kind,
                arm_label=e.arm_label,
                arm_index=e.arm_index,
                group_id=e.group_id,
                confidence=e.confidence,
            )
            for e in drafts
        ]

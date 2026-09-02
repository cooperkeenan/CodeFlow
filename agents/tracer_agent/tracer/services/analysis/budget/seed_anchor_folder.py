from tracer.models.pillar_scores import PillarScores
from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph

from shared.models.flow_graph import FlowNode

_SEED_PREFIX = "entry:seed:"


class SeedAnchorFolder:
    def __init__(self, keep_per_lane: int) -> None:
        self._keep = max(keep_per_lane, 1)

    def fold(self, graph: BudgetWorkGraph, pillars: PillarScores) -> None:
        by_lane: dict[str, list[FlowNode]] = {}
        for node_id in sorted(graph.nodes):
            node = graph.nodes[node_id]
            if node.level == 0 and node_id.startswith(_SEED_PREFIX):
                by_lane.setdefault(node.lane, []).append(node)
        for lane_id in sorted(by_lane):
            self._fold_lane(graph, by_lane[lane_id], pillars)

    def _fold_lane(
        self, graph: BudgetWorkGraph, anchors: list[FlowNode], pillars: PillarScores
    ) -> None:
        ordered = sorted(anchors, key=lambda node: self._rank(graph, node, pillars))
        if len(ordered) <= self._keep:
            return
        host = ordered[0]
        for node in ordered[self._keep :]:
            node.level = 1
            graph.add_edge(host.id, node.id, "sequence")

    def _rank(
        self, graph: BudgetWorkGraph, node: FlowNode, pillars: PillarScores
    ) -> tuple[float, int, str]:
        component = node.id[len(_SEED_PREFIX) :]
        return (-pillars.score(component), -len(graph.out_edges(node.id)), node.id)

from services.analysis.budget_work_graph import BudgetWorkGraph
from shared.models.flow_graph import FlowNode

_PRIORITY = {"effect": 0, "parallel": 1, "step": 2}


class LaneReducer:
    def reduce(
        self,
        graph: BudgetWorkGraph,
        lane_id: str,
        budget: int,
        spine: frozenset[str] = frozenset(),
    ) -> None:
        while graph.lane_node_count(lane_id) > budget:
            node_id = self._pick(graph, lane_id, spine)
            if node_id is None:
                return
            self._fold(graph, node_id)

    def _pick(self, graph: BudgetWorkGraph, lane_id: str, spine: frozenset[str]) -> str | None:
        protected: set[str] = set(spine)
        for edge in graph.edges.values():
            if edge.kind == "arm":
                protected.add(edge.target)
            elif edge.kind == "stitch":
                protected.add(edge.source)
                protected.add(edge.target)
        candidates = [
            node
            for node in graph.nodes.values()
            if node.lane == lane_id and node.kind in _PRIORITY and node.id not in protected
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda node: self._rank(graph, node)).id

    def _rank(self, graph: BudgetWorkGraph, node: FlowNode) -> tuple[int, int, int, str]:
        return (_PRIORITY[node.kind], len(graph.out_edges(node.id)), len(node.backing), node.id)

    def _fold(self, graph: BudgetWorkGraph, node_id: str) -> None:
        node = graph.nodes[node_id]
        preds = sorted({edge.source for edge in graph.in_edges(node_id)})
        succs = sorted({edge.target for edge in graph.out_edges(node_id)})
        target = self._credit_target(graph, preds)
        if target is not None:
            graph.nodes[target].folded_count += 1 + node.folded_count
        for pred in preds:
            for succ in succs:
                graph.add_edge(pred, succ, "sequence")
        graph.remove_node(node_id)

    def _credit_target(self, graph: BudgetWorkGraph, preds: list[str]) -> str | None:
        steps = [p for p in preds if graph.nodes.get(p) is not None and graph.nodes[p].kind == "step"]
        if steps:
            return steps[0]
        return preds[0] if preds else None

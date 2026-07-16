from services.analysis.budget_work_graph import BudgetWorkGraph
from shared.models.flow_graph import FlowNode


class DecisionDissolver:
    def dissolve(self, graph: BudgetWorkGraph, node_id: str) -> None:
        node = graph.nodes.get(node_id)
        if node is None or node.kind != "decision":
            return
        num_arms = len(graph.arm_edges(node_id))
        target_id = self._surrounding_step(graph, node_id)
        if target_id is None:
            self._inplace(graph, node, num_arms)
            return
        self._contract(graph, node, graph.nodes[target_id], num_arms)
        graph.prune_unreachable()

    def _surrounding_step(self, graph: BudgetWorkGraph, node_id: str) -> str | None:
        steps = [
            edge.source
            for edge in graph.in_edges(node_id)
            if graph.nodes.get(edge.source) is not None and graph.nodes[edge.source].kind == "step"
        ]
        return sorted(steps)[0] if steps else None

    def _contract(
        self, graph: BudgetWorkGraph, node: FlowNode, target: FlowNode, num_arms: int
    ) -> None:
        region = graph.reachable() - graph.reachable(frozenset({node.id})) - {node.id}
        for fqn in node.backing:
            if fqn not in target.backing:
                target.backing.append(fqn)
        target.refs.extend(node.refs)
        target.badges = sorted(set(target.badges) | set(node.badges))
        target.folded_count += num_arms
        graph.remove_node(node.id)
        for member in sorted(region):
            graph.remove_node(member)

    def _inplace(self, graph: BudgetWorkGraph, node: FlowNode, num_arms: int) -> None:
        node.kind = "step"
        node.folded_count += num_arms
        for edge in graph.arm_edges(node.id):
            graph.remove_edge(edge)
            graph.add_edge(edge.source, edge.target, "sequence")

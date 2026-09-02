from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph


class SequenceChainer:
    def link(self, graph: BudgetWorkGraph) -> None:
        bodies = self._bodies(graph)
        for owner in sorted(bodies):
            self._link_body(graph, bodies[owner])

    def _bodies(self, graph: BudgetWorkGraph) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for node_id in sorted(graph.nodes):
            for container in graph.nodes[node_id].containers:
                grouped.setdefault(container, []).append(node_id)
        return grouped

    def _link_body(self, graph: BudgetWorkGraph, members: list[str]) -> None:
        ordered = sorted(members, key=lambda m: self._sort_key(graph, m))
        for source, target in zip(ordered, ordered[1:]):
            self._maybe_link(graph, source, target)

    def _maybe_link(self, graph: BudgetWorkGraph, source: str, target: str) -> None:
        src, tgt = graph.nodes[source], graph.nodes[target]
        if src.kind == "outcome" or not src.owner_fqn or src.owner_fqn != tgt.owner_fqn:
            return
        if len(graph.arm_edges(source)) > 1:
            return
        if any(edge.target == target for edge in graph.out_edges(source)):
            return
        graph.add_edge(source, target, "sequence")

    def _sort_key(self, graph: BudgetWorkGraph, node_id: str) -> tuple[str, int, str]:
        refs = graph.nodes[node_id].refs
        if refs:
            return (refs[0].file, refs[0].line, node_id)
        return ("", 0, node_id)

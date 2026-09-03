from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph
from tracer.services.analysis.graph_ops import bodies_by_container, ref_sort_key


class SequenceChainer:
    def link(self, graph: BudgetWorkGraph) -> None:
        bodies = bodies_by_container(graph.nodes)
        for owner in sorted(bodies):
            self._link_body(graph, bodies[owner])

    def _link_body(self, graph: BudgetWorkGraph, members: list[str]) -> None:
        ordered = sorted(members, key=lambda m: ref_sort_key(graph.nodes, m))
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

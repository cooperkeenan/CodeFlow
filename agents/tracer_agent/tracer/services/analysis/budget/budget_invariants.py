from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph
from tracer.services.analysis.budget.containment_invariants import ContainmentInvariants


class BudgetInvariantChecker:
    def __init__(self, containment: ContainmentInvariants) -> None:
        self._containment = containment

    def enforce_containment(self, graph: BudgetWorkGraph) -> None:
        self._containment.enforce_structure(graph)

    def border_count(self, graph: BudgetWorkGraph) -> int:
        return self._containment.border_count(graph)

    def flow_list_split(self, graph: BudgetWorkGraph) -> tuple[int, int]:
        return self._containment.flow_list_split(graph)

    def enforce(self, graph: BudgetWorkGraph) -> None:
        self._drop_dangling(graph)
        self._assert_hidden_paths(graph)
        self._assert_reachable(graph)
        self._containment.enforce_bodies(graph)

    def _drop_dangling(self, graph: BudgetWorkGraph) -> None:
        for edge in list(graph.edges.values()):
            if edge.source not in graph.nodes or edge.target not in graph.nodes:
                graph.remove_edge(edge)

    def _assert_hidden_paths(self, graph: BudgetWorkGraph) -> None:
        for key in sorted(graph.edges):
            edge = graph.edges[key]
            if not edge.hidden_path:
                continue
            for node_id in edge.hidden_path:
                node = graph.nodes.get(node_id)
                assert node is not None, f"hidden_path references missing node {node_id}"
                assert node.level >= 1, f"hidden_path node {node_id} is not hidden"
            for endpoint in (edge.source, edge.target):
                level = graph.nodes[endpoint].level
                assert level == 0, f"skeleton edge endpoint {endpoint} is level {level}"

    def _assert_reachable(self, graph: BudgetWorkGraph) -> None:
        reachable = graph.reachable()
        stranded = sorted(node_id for node_id in graph.nodes if node_id not in reachable)
        assert not stranded, f"{len(stranded)} nodes unreachable from any entry: {stranded[:5]}"

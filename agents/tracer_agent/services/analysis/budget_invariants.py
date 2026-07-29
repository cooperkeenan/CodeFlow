from services.analysis.budget_config import BudgetConfig
from services.analysis.budget_work_graph import BudgetWorkGraph


class BudgetInvariantChecker:
    def __init__(self, config: BudgetConfig) -> None:
        self._config = config

    def enforce(self, graph: BudgetWorkGraph) -> None:
        self._drop_dangling(graph)
        graph.prune_unreachable()
        self._drop_dangling(graph)
        self._assert(graph)

    def _drop_dangling(self, graph: BudgetWorkGraph) -> None:
        for edge in list(graph.edges.values()):
            if edge.source not in graph.nodes or edge.target not in graph.nodes:
                graph.remove_edge(edge)

    def _assert(self, graph: BudgetWorkGraph) -> None:
        ceiling = self._config.node_budget + len(graph.lanes) * self._config.min_lane_nodes
        assert len(graph.nodes) <= ceiling, f"node budget exceeded: {len(graph.nodes)} > {ceiling}"
        for node in graph.nodes.values():
            if node.kind == "decision":
                arms = len(graph.arm_edges(node.id))
                assert arms >= 1, f"decision {node.id} retains {arms} arm edges"
        reachable = graph.reachable()
        for node_id in graph.nodes:
            assert node_id in reachable, f"node {node_id} unreachable from any entry"

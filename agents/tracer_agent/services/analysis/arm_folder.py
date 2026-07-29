from services.analysis.budget_config import BudgetConfig
from services.analysis.budget_work_graph import BudgetWorkGraph
from shared.models.flow_graph import FlowEdge, FlowNode


class ArmFolder:
    def __init__(self, config: BudgetConfig) -> None:
        self._config = config

    def fold(self, graph: BudgetWorkGraph) -> None:
        for node_id in sorted(n.id for n in graph.nodes.values() if n.kind == "decision"):
            self._fold_node(graph, node_id)

    def _fold_node(self, graph: BudgetWorkGraph, node_id: str) -> None:
        arms = graph.arm_edges(node_id)
        if len(arms) <= self._config.max_arms_per_decision:
            return
        ranked = sorted(arms, key=lambda edge: (-self._reach(graph, edge.target), edge.target))
        drop = ranked[self._config.max_arms_per_decision - 1 :]
        self._collapse(graph, node_id, drop)

    def _collapse(self, graph: BudgetWorkGraph, node_id: str, drop: list[FlowEdge]) -> None:
        node = graph.nodes[node_id]
        fold_id = f"fold:{node_id}"
        label = f"+{len(drop)} more"
        backing: list[str] = []
        for edge in drop:
            target = graph.nodes.get(edge.target)
            for fqn in target.backing if target is not None else []:
                if fqn not in backing:
                    backing.append(fqn)
            graph.remove_edge(edge)
        graph.nodes[fold_id] = FlowNode(
            id=fold_id, kind="step", lane=node.lane, label=label,
            backing=backing, folded_count=len(drop), badges=["folded"],
        )
        graph.add_edge(node_id, fold_id, "arm", label)
        graph.prune_unreachable()

    def _reach(self, graph: BudgetWorkGraph, start: str) -> int:
        return len(graph.reachable_from(start))

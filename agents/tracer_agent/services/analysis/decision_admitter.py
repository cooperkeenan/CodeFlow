from models.significance_result import SignificanceResult
from services.analysis.budget_recondenser import BudgetRecondenser
from services.analysis.budget_work_graph import BudgetWorkGraph
from services.analysis.decision_dissolver import DecisionDissolver
from services.analysis.lane_reducer import LaneReducer


class DecisionAdmitter:
    def __init__(
        self, recondenser: BudgetRecondenser, dissolver: DecisionDissolver, reducer: LaneReducer
    ) -> None:
        self._recondenser = recondenser
        self._dissolver = dissolver
        self._reducer = reducer

    def admit(
        self, graph: BudgetWorkGraph, budgets: dict[str, int], significance: SignificanceResult
    ) -> None:
        self._dissolve_thin(graph)
        self._recondenser.recondense(graph)
        for lane in sorted(graph.lanes, key=lambda lane: lane.id):
            self._admit_lane(graph, lane.id, budgets.get(lane.id, 0), significance)

    def _admit_lane(
        self, graph: BudgetWorkGraph, lane_id: str, budget: int, significance: SignificanceResult
    ) -> None:
        queue = self._lane_decisions(graph, lane_id, significance)
        while graph.lane_node_count(lane_id) > budget and queue:
            self._dissolver.dissolve(graph, queue.pop(0))
            self._recondenser.recondense(graph)
        self._reducer.reduce(graph, lane_id, budget)
        self._recondenser.recondense(graph)

    def _lane_decisions(
        self, graph: BudgetWorkGraph, lane_id: str, significance: SignificanceResult
    ) -> list[str]:
        decisions = [
            node
            for node in graph.nodes.values()
            if node.kind == "decision" and node.lane == lane_id
        ]
        ordered = sorted(decisions, key=lambda node: (self._score(node.id, significance), node.id))
        return [node.id for node in ordered]

    def _score(self, node_id: str, significance: SignificanceResult) -> float:
        verdict = significance.verdicts.get(node_id[4:])
        return verdict.score if verdict is not None else 0.0

    def _dissolve_thin(self, graph: BudgetWorkGraph) -> None:
        thin = [
            node
            for node in sorted(graph.nodes.values(), key=lambda node: node.id)
            if node.kind == "decision" and len(graph.arm_edges(node.id)) < 2
        ]
        for node in thin:
            self._dissolver.dissolve(graph, node.id)

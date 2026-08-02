from models.significance_result import SignificanceResult
from services.analysis.budget_recondenser import BudgetRecondenser
from services.analysis.budget_work_graph import BudgetWorkGraph
from services.analysis.decision_dissolver import DecisionDissolver
from services.analysis.lane_reducer import LaneReducer
from services.analysis.spine_protector import SpineProtector


class DecisionAdmitter:
    def __init__(
        self,
        recondenser: BudgetRecondenser,
        dissolver: DecisionDissolver,
        reducer: LaneReducer,
        spine: SpineProtector,
        visible_decisions: int,
    ) -> None:
        self._recondenser = recondenser
        self._dissolver = dissolver
        self._reducer = reducer
        self._spine = spine
        self._visible_decisions = visible_decisions

    def admit(
        self, graph: BudgetWorkGraph, budgets: dict[str, int], significance: SignificanceResult
    ) -> None:
        self._dissolve_thin(graph)
        self._recondenser.recondense(graph)
        self._dissolve_unranked(graph, significance)
        self._recondenser.recondense(graph)
        spine = self._spine.compute(graph)
        for lane in sorted(graph.lanes, key=lambda lane: lane.id):
            self._admit_lane(graph, lane.id, budgets.get(lane.id, 0), significance, spine)

    def sweep_orphaned(self, graph: BudgetWorkGraph) -> None:
        while self._dissolve_thin(graph):
            self._recondenser.recondense(graph)

    def _dissolve_unranked(
        self, graph: BudgetWorkGraph, significance: SignificanceResult
    ) -> None:
        while True:
            surviving = self._surviving_ranked(graph, significance)
            if len(surviving) <= self._visible_decisions:
                return
            self._dissolver.dissolve(graph, f"dec:{surviving[-1]}")
            self._recondenser.recondense(graph)
            self._dissolve_thin(graph)
            self._recondenser.recondense(graph)

    def _surviving_ranked(
        self, graph: BudgetWorkGraph, significance: SignificanceResult
    ) -> list[str]:
        return [
            site_id
            for site_id in significance.ranked_decisions
            if self._is_live_decision(graph, f"dec:{site_id}")
        ]

    def _is_live_decision(self, graph: BudgetWorkGraph, node_id: str) -> bool:
        node = graph.nodes.get(node_id)
        return node is not None and node.kind == "decision"

    def _admit_lane(
        self,
        graph: BudgetWorkGraph,
        lane_id: str,
        budget: int,
        significance: SignificanceResult,
        spine: frozenset[str],
    ) -> None:
        self._reducer.reduce(graph, lane_id, budget, spine)
        self._recondenser.recondense(graph)
        queue = self._lane_decisions(graph, lane_id, significance, spine)
        while graph.lane_node_count(lane_id) > budget and queue:
            self._dissolver.dissolve(graph, queue.pop(0))
            self._recondenser.recondense(graph)

    def _lane_decisions(
        self,
        graph: BudgetWorkGraph,
        lane_id: str,
        significance: SignificanceResult,
        spine: frozenset[str],
    ) -> list[str]:
        decisions = [
            node
            for node in graph.nodes.values()
            if node.kind == "decision" and node.lane == lane_id
        ]
        ordered = sorted(
            decisions,
            key=lambda node: (node.id in spine, self._score(node.id, significance), node.id),
        )
        return [node.id for node in ordered]

    def _score(self, node_id: str, significance: SignificanceResult) -> tuple[float, float]:
        verdict = significance.verdicts.get(node_id[4:])
        if verdict is None:
            return (0.0, 0.0)
        return (verdict.importance, verdict.score)

    def _dissolve_thin(self, graph: BudgetWorkGraph) -> bool:
        thin = [
            node
            for node in sorted(graph.nodes.values(), key=lambda node: node.id)
            if node.kind == "decision" and len(graph.arm_edges(node.id)) == 0
        ]
        for node in thin:
            self._dissolver.dissolve(graph, node.id)
        return bool(thin)

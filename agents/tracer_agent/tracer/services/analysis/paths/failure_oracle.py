import ast

from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.paths.arm_signal_index import ArmSignalIndex
from tracer.services.analysis.paths.path_graph import PathGraph
from tracer.services.analysis.syntax.arm_outcome import classify_outcome

from shared.models.flow_graph import FlowEdge


class FailureOracle:
    def __init__(self, arms: ArmSignalIndex, index: ProjectIndex, graph: PathGraph) -> None:
        self._arms = arms
        self._index = index
        self._graph = graph
        self._returns: dict[str, bool] = {}

    def is_failure(self, edge: FlowEdge) -> bool:
        if edge.kind == "arm":
            arm = self._arms.arm(edge.group_id, edge.arm_index)
            if arm is not None and arm.outcome == "failure":
                return True
        return self._is_failing_return(edge.target)

    def _is_failing_return(self, node_id: str) -> bool:
        if not node_id.startswith("ret:"):
            return False
        if node_id not in self._returns:
            self._returns[node_id] = self._classify(node_id)
        return self._returns[node_id]

    def _classify(self, node_id: str) -> bool:
        fqn = self._graph.owner(node_id)
        record = self._index.functions.get(fqn)
        body = getattr(record, "body", None)
        if body is None:
            return False
        line = int(node_id.rsplit(":", 1)[1])
        for stmt in ast.walk(body):
            if isinstance(stmt, (ast.Return, ast.Raise)) and stmt.lineno == line:
                return classify_outcome([stmt]) == "failure"
        return False

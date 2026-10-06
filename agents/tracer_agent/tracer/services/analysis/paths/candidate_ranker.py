import re

from tracer.services.analysis.paths.arm_signal_index import ArmSignalIndex
from tracer.services.analysis.paths.failure_oracle import FailureOracle
from tracer.services.analysis.paths.reach_counter import ReachCounter

from shared.models.flow_graph import FlowEdge

_METHOD_TEST = re.compile(r"method\s*==\s*['\"](\w+)['\"]")
_NON_VERBS = frozenset({"", "ANY"})
_EARLY_EXITS = frozenset({"returns", "raises"})


class CandidateRanker:
    def __init__(self, arms: ArmSignalIndex, oracle: FailureOracle, reach: ReachCounter) -> None:
        self._arms = arms
        self._oracle = oracle
        self._reach = reach

    def choose(
        self,
        edges: list[FlowEdge],
        owners: frozenset[str],
        visited: set[str],
        verb: str,
        own_head: str,
    ) -> tuple[FlowEdge | None, bool]:
        if not edges:
            return None, False
        ok = [e for e in edges if not self._oracle.is_failure(e)]
        forced = not ok
        pool = self._by_verb(ok or edges, verb)
        scored = [
            (
                -self._reach.count(e.target, owners, visited, own_head),
                e.target.startswith("out:"),
                self._oracle.is_implicit_terminal(e.target),
                self._exits_early(e),
                e.arm_index < 0,
                e.arm_index,
                e.target,
                e,
            )
            for e in pool
        ]
        scored.sort(key=lambda s: s[:7])
        return scored[0][7], forced

    def _exits_early(self, edge: FlowEdge) -> bool:
        if edge.kind != "arm":
            return False
        arm = self._arms.arm(edge.group_id, edge.arm_index)
        return arm is not None and arm.terminal in _EARLY_EXITS

    def _by_verb(self, edges: list[FlowEdge], verb: str) -> list[FlowEdge]:
        wanted = verb.upper()
        if wanted in _NON_VERBS:
            return edges
        tested = {id(e): self._tested_verb(e) for e in edges}
        matching = [e for e in edges if tested[id(e)] == wanted]
        if matching:
            return matching
        neutral = [e for e in edges if tested[id(e)] is None]
        return neutral or edges

    def _tested_verb(self, edge: FlowEdge) -> str | None:
        if edge.kind != "arm":
            return None
        arm = self._arms.arm(edge.group_id, edge.arm_index)
        found = _METHOD_TEST.search(arm.label_source) if arm else None
        return found.group(1).upper() if found else None

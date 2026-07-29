from models.arm import Arm
from services.analysis.call_graph import CallGraph
from services.analysis.component_index import ComponentIndex
from services.analysis.scc_index import SccIndex


class ReachComputer:
    def __init__(
        self,
        graph: CallGraph,
        scc: SccIndex,
        components: ComponentIndex,
        utilities: frozenset[str],
    ) -> None:
        self._graph = graph
        self._scc = scc
        self._components = components
        self._utilities = utilities
        self._memo: dict[int, frozenset[str]] = {}

    def reach_of(self, fqn: str) -> frozenset[str]:
        scc = self._scc.scc_of(fqn)
        if scc is None:
            return frozenset()
        return self._reach_scc(scc, frozenset())

    def arm_reach(self, arm: Arm, owner_component: str | None) -> frozenset[str]:
        acc: set[str] = set()
        for callsite in arm.callsites:
            for target in callsite.targets:
                acc |= self.reach_of(target.fqn)
        acc -= self._utilities
        if owner_component is not None:
            acc.discard(owner_component)
        return frozenset(acc)

    def _reach_scc(self, scc: int, active: frozenset[int]) -> frozenset[str]:
        cached = self._memo.get(scc)
        if cached is not None:
            return cached
        collected: set[str] = set(self._own_components(scc))
        for successor in self._successor_sccs(scc):
            if successor in active or successor == scc:
                continue
            collected |= self._reach_scc(successor, active | {scc})
        result = frozenset(collected)
        if not (active & self._successor_sccs(scc)):
            self._memo[scc] = result
        return result

    def _own_components(self, scc: int) -> frozenset[str]:
        return frozenset(
            component
            for node in self._scc.members_of(scc)
            for component in (self._components.component_of(node),)
            if component is not None
        )

    def _successor_sccs(self, scc: int) -> frozenset[int]:
        return frozenset(
            target
            for node in self._scc.members_of(scc)
            for successor in self._graph.successors(node)
            for target in (self._scc.scc_of(successor),)
            if target is not None
        )

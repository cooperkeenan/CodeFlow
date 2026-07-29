from collections.abc import Mapping

from models.call_site import CallSite
from services.analysis.component_index import ComponentIndex


class CallGraph:
    def __init__(self, adjacency: Mapping[str, frozenset[str]]) -> None:
        self._adjacency = adjacency

    def successors(self, fqn: str) -> frozenset[str]:
        return self._adjacency.get(fqn, frozenset())

    @property
    def nodes(self) -> frozenset[str]:
        return frozenset(self._adjacency)


class CallGraphBuilder:
    def __init__(self, components: ComponentIndex) -> None:
        self._components = components

    def build(self, callsites: tuple[CallSite, ...]) -> CallGraph:
        adjacency: dict[str, set[str]] = {}
        for site in callsites:
            edges = adjacency.setdefault(site.caller, set())
            for target in site.targets:
                if self._components.is_project_target(target.fqn):
                    edges.add(target.fqn)
        return CallGraph({fqn: frozenset(succ) for fqn, succ in adjacency.items()})

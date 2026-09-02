from tracer.models.sites import DispatchSite
from tracer.services.analysis.resolve.call_graph import CallGraph

_STRUCTURAL_KINDS = frozenset({"route"})


class RouteReachIndex:
    def __init__(self, reachable: frozenset[str]) -> None:
        self._reachable = reachable

    def is_route_reachable(self, fqn: str) -> bool:
        return fqn in self._reachable


class RouteReachIndexBuilder:
    def build(self, sites: tuple[DispatchSite, ...], graph: CallGraph) -> RouteReachIndex:
        entries = {
            callsite.caller
            for site in sites
            if site.kind in _STRUCTURAL_KINDS
            for arm in site.arms
            for callsite in arm.callsites
        }
        reachable: set[str] = set()
        frontier = list(entries)
        while frontier:
            node = frontier.pop()
            if node in reachable:
                continue
            reachable.add(node)
            frontier.extend(graph.successors(node))
        return RouteReachIndex(frozenset(reachable))

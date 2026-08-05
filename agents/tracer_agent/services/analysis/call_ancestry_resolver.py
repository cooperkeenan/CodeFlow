from collections.abc import Mapping

from models.call_site import CallSite


class CallAncestryResolver:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        callers: dict[str, set[str]] = {}
        for site in callsites:
            for target in site.targets:
                callers.setdefault(target.fqn, set()).add(site.caller)
        self._callers = {fqn: frozenset(c) for fqn, c in callers.items()}

    def nearest_ancestor(self, fqn: str, in_graph: Mapping[str, str]) -> str | None:
        seen = {fqn}
        frontier = sorted(self._callers.get(fqn, ()))
        while frontier:
            next_frontier: set[str] = set()
            for candidate in frontier:
                if candidate in in_graph:
                    return in_graph[candidate]
                if candidate in seen:
                    continue
                seen.add(candidate)
                next_frontier.update(self._callers.get(candidate, ()))
            frontier = sorted(next_frontier)
        return None

from tracer.services.analysis.paths.path_graph import PathGraph

_REGION_CAP = 300


class HopFinder:
    def __init__(self, graph: PathGraph) -> None:
        self._graph = graph

    def resume(
        self,
        hop_id: str,
        owners: frozenset[str],
        visited: set[str],
        own_head: str,
        pred_line: int,
    ) -> str | None:
        seen = {hop_id}
        level = [hop_id]
        while level and len(seen) <= _REGION_CAP:
            found: set[str] = set()
            following: set[str] = set()
            for current in level:
                for edge in self._graph.out(current):
                    target = edge.target
                    if self._graph.is_entry(target):
                        continue
                    if self._graph.owner(target) in owners:
                        if target not in visited and self._graph.is_walkable_target(
                            target, own_head
                        ):
                            found.add(target)
                    elif target not in seen:
                        following.add(target)
            if found:
                return min(found, key=lambda t: (self._graph.line(t) < pred_line, self._graph.line(t), t))
            seen |= following
            level = sorted(following)
        return None

from tracer.services.analysis.paths.path_graph import PathGraph

_REGION_CAP = 300


class ReachCounter:
    def __init__(self, graph: PathGraph) -> None:
        self._graph = graph

    def count(self, start: str, owners: frozenset[str], blocked: set[str], own_head: str) -> int:
        seen = {start}
        queue = [start]
        total = 0
        while queue:
            current = queue.pop(0)
            if self._graph.owner(current) in owners:
                total += 1
            for edge in self._graph.out(current):
                target = edge.target
                if target in seen or self._graph.is_entry(target):
                    continue
                if self._graph.owner(target) in owners:
                    if target in blocked or not self._graph.is_walkable_target(target, own_head):
                        continue
                elif len(seen) >= _REGION_CAP:
                    continue
                seen.add(target)
                queue.append(target)
        return total

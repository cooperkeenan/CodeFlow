from tracer.services.analysis.paths.path_graph import PathGraph


class ReachCounter:
    def __init__(self, graph: PathGraph) -> None:
        self._graph = graph

    def count(self, start: str, owners: frozenset[str], blocked: set[str], own_head: str) -> int:
        seen = {start}
        queue = [start]
        total = 0
        while queue:
            current = queue.pop(0)
            owned = self._graph.owner(current) in owners
            if owned:
                total += 1
            if not owned and current != start:
                continue
            for edge in self._graph.out(current):
                target = edge.target
                if target in seen or target in blocked:
                    continue
                if not self._graph.is_walkable_target(target, own_head):
                    continue
                seen.add(target)
                queue.append(target)
        return total

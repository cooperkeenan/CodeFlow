from typing import Mapping, Protocol


class _Containered(Protocol):
    containers: list[str]


class ContainerCycleGuard:
    def creates_cycle(self, nodes: Mapping[str, _Containered], node_id: str, container: str) -> bool:
        return self._is_descendant(nodes, container, node_id)

    def _is_descendant(
        self, nodes: Mapping[str, _Containered], node_id: str, ancestor: str
    ) -> bool:
        seen = {node_id}
        frontier = list(nodes[node_id].containers) if node_id in nodes else []
        while frontier:
            next_frontier: list[str] = []
            for candidate in frontier:
                if candidate == ancestor:
                    return True
                if candidate in seen or candidate not in nodes:
                    continue
                seen.add(candidate)
                next_frontier.extend(nodes[candidate].containers)
            frontier = next_frontier
        return False

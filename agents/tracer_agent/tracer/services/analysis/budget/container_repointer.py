from typing import Mapping, Protocol


class _Containered(Protocol):
    containers: list[str]


class ContainerRepointer:
    def repoint(self, nodes: Mapping[str, _Containered], keep: str, other: str) -> None:
        for node_id in sorted(nodes):
            if node_id == other:
                continue
            node = nodes[node_id]
            if other in node.containers:
                node.containers.remove(other)
                if (
                    keep != node_id
                    and keep not in node.containers
                    and not self._is_descendant(nodes, keep, node_id)
                ):
                    node.containers.append(keep)
                node.containers.sort()

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

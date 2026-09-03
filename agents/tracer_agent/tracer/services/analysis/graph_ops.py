from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol

from shared.models.flow_graph import SourceRef


class Containered(Protocol):
    containers: list[str]


class Anchored(Protocol):
    refs: Sequence[SourceRef]


def bodies_by_container(nodes: Mapping[str, Containered]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for node_id in sorted(nodes):
        for container in nodes[node_id].containers:
            grouped.setdefault(container, []).append(node_id)
    return grouped


def ref_sort_key(nodes: Mapping[str, Anchored], node_id: str) -> tuple[str, int, str]:
    refs = nodes[node_id].refs
    if refs:
        return (refs[0].file, refs[0].line, node_id)
    return ("", 0, node_id)


def is_descendant(nodes: Mapping[str, Containered], node_id: str, ancestor: str) -> bool:
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


def dedup(values: Iterable[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        seen.setdefault(value, None)
    return list(seen)

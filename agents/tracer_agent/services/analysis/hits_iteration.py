from collections.abc import Mapping


def run_hits(
    adjacency: Mapping[str, Mapping[str, int]],
    nodes: frozenset[str],
    iterations: int,
    decimals: int,
) -> tuple[dict[str, float], dict[str, float]]:
    ordered = sorted(nodes)
    hub = {node: 1.0 for node in ordered}
    authority = {node: 1.0 for node in ordered}
    destinations = sorted(adjacency)
    for _ in range(iterations):
        next_authority = {node: 0.0 for node in ordered}
        for dest in destinations:
            sources = adjacency[dest]
            for source in sorted(sources):
                next_authority[dest] += hub[source] * sources[source]
        next_hub = {node: 0.0 for node in ordered}
        for dest in destinations:
            sources = adjacency[dest]
            for source in sorted(sources):
                next_hub[source] += next_authority[dest] * sources[source]
        authority = _normalise(next_authority, ordered)
        hub = _normalise(next_hub, ordered)
    return (
        {node: round(hub[node], decimals) for node in ordered},
        {node: round(authority[node], decimals) for node in ordered},
    )


def _normalise(values: dict[str, float], ordered: list[str]) -> dict[str, float]:
    total = 0.0
    for node in ordered:
        total += values[node]
    if total <= 0.0:
        return values
    return {node: values[node] / total for node in ordered}

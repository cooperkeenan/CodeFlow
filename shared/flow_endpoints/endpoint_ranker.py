from shared.flow_endpoints.slice_graph import SliceGraph

_KIND_RANK = {"entry": 0, "decision": 1, "parallel": 2, "effect": 3, "outcome": 4, "step": 5}


class EndpointRanker:
    def __init__(self, exclusivity: dict[str, int] | None = None) -> None:
        self._exclusivity = exclusivity or {}

    def select(self, graph: SliceGraph, budget: int) -> set[str]:
        distance = self._distance(graph)
        candidates = sorted(
            graph.keep,
            key=lambda node_id: (
                distance.get(node_id, 10**6),
                _KIND_RANK.get(graph.nodes[node_id].kind, 9),
                self._exclusivity.get(graph.nodes[node_id].owner_fqn, 1),
                -graph.out_degree(node_id),
                node_id,
            ),
        )
        chosen = {graph.root_id}
        for node_id in candidates:
            if len(chosen) >= budget:
                break
            if node_id in chosen:
                continue
            if self._reachable(graph, node_id, chosen, distance):
                chosen.add(node_id)
        return chosen

    def _reachable(
        self, graph: SliceGraph, node_id: str, chosen: set[str], distance: dict[str, int]
    ) -> bool:
        parents = graph.predecessors(node_id)
        if not parents:
            return True
        return any(parent in chosen for parent in parents)

    def _distance(self, graph: SliceGraph) -> dict[str, int]:
        distance = {graph.root_id: 0}
        frontier = [graph.root_id]
        while frontier:
            nxt: list[str] = []
            for node_id in frontier:
                for target in graph.successors(node_id):
                    if target not in distance:
                        distance[target] = distance[node_id] + 1
                        nxt.append(target)
            frontier = nxt
        return distance

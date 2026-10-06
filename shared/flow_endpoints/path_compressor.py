from shared.flow_endpoints.run_collapser import RunCollapser
from shared.flow_endpoints.slice_graph import SliceGraph


class PathCompressor:
    def __init__(self, runs: RunCollapser) -> None:
        self._runs = runs

    def compress(self, graph: SliceGraph, budget: int) -> None:
        path = list(dict.fromkeys(graph.path()))
        excess = len(path) - (budget - 1)
        interior = path[1:-1]
        if excess <= 0 or len(interior) < 2:
            return
        size = min(excess + 1, len(interior))
        starts = range(len(interior) - size + 1)
        best = min(starts, key=lambda s: (self._forks(graph, interior[s : s + size]), s))
        window = [n for n in interior[best : best + size] if n in graph.keep]
        if len(window) >= 2:
            self._runs.fold(graph, window)

    def _forks(self, graph: SliceGraph, window: list[str]) -> int:
        return sum(1 for node_id in window if graph.nodes[node_id].kind == "decision")

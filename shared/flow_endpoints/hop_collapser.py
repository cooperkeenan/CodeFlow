from shared.flow_endpoints.shared_helper_collapser import HELPER_PREFIX, SharedHelperCollapser
from shared.flow_endpoints.slice_graph import SliceGraph


class HopCollapser:
    def __init__(self, helpers: SharedHelperCollapser) -> None:
        self._helpers = helpers

    def collapse(
        self, graph: SliceGraph, regions: dict[str, list[str]], path: list[str], hops: list[str]
    ) -> None:
        for hop in hops:
            region = regions.get(hop)
            if not region or hop not in graph.nodes or hop not in graph.keep:
                continue
            owner = graph.nodes[hop].owner_fqn
            if not owner or f"{HELPER_PREFIX}{owner}" in graph.nodes:
                continue
            rest = sorted(m for m in region if m != hop and m in graph.keep)
            self._helpers.fold(graph, owner, [hop] + rest)
            self._resume(graph, path, hop)

    def _resume(self, graph: SliceGraph, path: list[str], hop: str) -> None:
        host = graph.resolve(hop)
        index = path.index(hop)
        for later in path[index + 1 :]:
            target = graph.resolve(later)
            if target != host and target in graph.nodes:
                graph.add_edge(host, target)
                return

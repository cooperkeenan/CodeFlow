from shared.flow_endpoints.level_assigner import LevelAssigner
from shared.flow_endpoints.slice_graph import SliceGraph

_MAX_ROUNDS = 4


class SoleChildPromoter:
    def promote(self, graph: SliceGraph, levels: LevelAssigner) -> None:
        for _ in range(_MAX_ROUNDS):
            promoted = self._sole_children(graph)
            if not promoted:
                return
            graph.keep.update(promoted)
            levels.assign(graph)

    def _sole_children(self, graph: SliceGraph) -> list[str]:
        found: set[str] = set()
        for node_id in sorted(graph.keep):
            children = graph.nodes[node_id].hidden_children
            if len(children) != 1:
                continue
            child = children[0]
            if child in graph.nodes and child not in graph.keep:
                found.add(child)
        return sorted(found)

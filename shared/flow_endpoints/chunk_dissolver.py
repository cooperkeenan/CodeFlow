from shared.flow_endpoints.slice_graph import SliceGraph

_SYNTHETIC_PREFIXES = ("more:", "fold:")


class ChunkDissolver:
    def dissolve(self, graph: SliceGraph) -> None:
        untouchable = graph.pinned | graph.protected
        for node_id in sorted(graph.nodes):
            if node_id.startswith(_SYNTHETIC_PREFIXES) and node_id != graph.root_id and node_id not in untouchable:
                graph.drop(node_id)

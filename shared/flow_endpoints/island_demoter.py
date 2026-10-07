from shared.flow_endpoints.slice_graph import SliceGraph


class IslandDemoter:
    def __init__(self, floor: int = 10) -> None:
        self._floor = floor

    def demote(self, graph: SliceGraph) -> None:
        connected = self._connected(graph)
        islands = sorted(node_id for node_id in graph.keep if node_id not in connected)
        for node_id in islands:
            if len(graph.keep) <= self._floor:
                return
            graph.keep.discard(node_id)
            if not graph.nodes[node_id].containers:
                graph.nodes[node_id].containers = [graph.root_id]

    def _connected(self, graph: SliceGraph) -> set[str]:
        seen = {graph.root_id}
        stack = [graph.root_id]
        while stack:
            current = stack.pop()
            for target in graph.successors(current):
                if target in graph.keep and target not in seen:
                    seen.add(target)
                    stack.append(target)
        return seen

from shared.flow_endpoints.slice_graph import SliceGraph

_KIND_RANK = {"entry": 0, "decision": 1, "parallel": 2, "effect": 3, "outcome": 4, "step": 5}


class FanoutCapper:
    def __init__(self, max_children: int = 5) -> None:
        self._max = max(max_children, 2)

    def cap(self, graph: SliceGraph) -> None:
        sizes = self._subtree_sizes(graph)
        for parent_id in sorted(graph.nodes):
            if parent_id not in graph.keep:
                continue
            children = [c for c in graph.successors(parent_id) if c in graph.keep]
            if len(children) <= self._max:
                continue
            children.sort(
                key=lambda child: (
                    _KIND_RANK.get(graph.nodes[child].kind, 9),
                    -sizes.get(child, 0),
                    child,
                )
            )
            for child_id in children[self._max :]:
                graph.keep.discard(child_id)
                graph.nodes[child_id].containers = [parent_id]

    def _subtree_sizes(self, graph: SliceGraph) -> dict[str, int]:
        sizes: dict[str, int] = {}
        for node_id in graph.nodes:
            seen: set[str] = set()
            stack = list(graph.successors(node_id))
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                stack.extend(graph.successors(current))
            sizes[node_id] = len(seen)
        return sizes

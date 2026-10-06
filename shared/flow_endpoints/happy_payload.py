from shared.flow_endpoints.slice_graph import SliceGraph


class HappyPayload:
    def build(self, graph: SliceGraph, ends_in_failure: bool) -> dict:
        resolved = graph.path()
        for node_id in resolved:
            if node_id not in graph.keep:
                raise ValueError(f"path node {node_id} is not visible")
        direct = {(e.source, e.target) for e in graph.edges}
        edges: list[list[str]] = []
        for source, target in zip(resolved, resolved[1:]):
            if (source, target) not in direct:
                raise ValueError(f"no direct edge {source} -> {target}")
            if [source, target] not in edges:
                edges.append([source, target])
        return {
            "node_ids": list(dict.fromkeys(resolved)),
            "edges": edges,
            "ends_in_failure": ends_in_failure,
        }

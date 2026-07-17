from collections import deque

from shared.models.flow_graph import FlowEdge, FlowNode


def _flow_adjacency(nodes: list[FlowNode], edges: list[FlowEdge]) -> dict[str, list[str]]:
    ids = {node.id for node in nodes}
    out: dict[str, list[str]] = {node.id: [] for node in nodes}
    for edge in edges:
        if edge.kind == "stitch":
            continue
        if edge.source in ids and edge.target in ids:
            out[edge.source].append(edge.target)
    return out


def reachable_counts(nodes: list[FlowNode], edges: list[FlowEdge]) -> dict[str, int]:
    adjacency = _flow_adjacency(nodes, edges)
    counts: dict[str, int] = {}
    for start in adjacency:
        seen: set[str] = set()
        stack = list(adjacency[start])
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency.get(current, ()))
        counts[start] = len(seen)
    return counts


def longest_path_depths(
    lane_nodes: list[FlowNode], edges: list[FlowEdge]
) -> dict[str, int]:
    adjacency = _flow_adjacency(lane_nodes, edges)
    indegree: dict[str, int] = {node.id: 0 for node in lane_nodes}
    for source in adjacency:
        for target in adjacency[source]:
            indegree[target] += 1
    depth: dict[str, int] = {node.id: 0 for node in lane_nodes}
    queue: deque[str] = deque(sorted(n for n, d in indegree.items() if d == 0))
    processed: set[str] = set()
    while queue:
        source = queue.popleft()
        processed.add(source)
        for target in adjacency[source]:
            if depth[target] < depth[source] + 1:
                depth[target] = depth[source] + 1
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    for node_id in sorted(indegree):
        if node_id not in processed:
            depth[node_id] = max(depth.values(), default=0)
    return depth

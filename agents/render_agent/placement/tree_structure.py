from dataclasses import dataclass

from shared.models.flow_graph import FlowEdge, FlowNode
from placement.flow_reach import reachable_counts


@dataclass(frozen=True)
class TreeForest:
    roots: list[str]
    children: dict[str, list[str]]


def _adjacency(nodes: list[FlowNode], edges: list[FlowEdge]) -> dict[str, list[str]]:
    ids = {node.id for node in nodes}
    out: dict[str, list[str]] = {node.id: [] for node in nodes}
    for edge in edges:
        if edge.source in ids and edge.target in ids:
            out[edge.source].append(edge.target)
    return out


def _indegree(nodes: list[FlowNode], adjacency: dict[str, list[str]]) -> dict[str, int]:
    indegree: dict[str, int] = {node.id: 0 for node in nodes}
    for source in adjacency:
        for target in adjacency[source]:
            indegree[target] += 1
    return indegree


def _decision_reach(nodes: list[FlowNode], adjacency: dict[str, list[str]]) -> dict[str, int]:
    kind_by_id = {node.id: node.kind for node in nodes}
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
        counts[start] = sum(1 for node_id in seen if kind_by_id.get(node_id) == "decision")
    return counts


def select_root(nodes: list[FlowNode], edges: list[FlowEdge]) -> str | None:
    if not nodes:
        return None
    adjacency = _adjacency(nodes, edges)
    entries = [node.id for node in nodes if node.kind == "entry"]
    if entries:
        decision_reach = _decision_reach(nodes, adjacency)
        return min(entries, key=lambda nid: (-decision_reach.get(nid, 0), nid))
    indegree = _indegree(nodes, adjacency)
    sources = [node.id for node in nodes if indegree.get(node.id, 0) == 0]
    if sources:
        subtree_size = reachable_counts(nodes, edges)
        return min(sources, key=lambda nid: (-subtree_size.get(nid, 0), nid))
    return min(node.id for node in nodes)


def _assign_parents(
    nodes: list[FlowNode], edges: list[FlowEdge], depths: dict[str, int]
) -> dict[str, str | None]:
    ids = {node.id for node in nodes}
    preds: dict[str, list[str]] = {node.id: [] for node in nodes}
    for edge in edges:
        if edge.source in ids and edge.target in ids:
            preds[edge.target].append(edge.source)
    parent: dict[str, str | None] = {}
    for node in nodes:
        candidates = [p for p in preds[node.id] if depths.get(p, 0) < depths.get(node.id, 0)]
        if not candidates:
            parent[node.id] = None
            continue
        best_depth = max(depths[p] for p in candidates)
        parent[node.id] = min(p for p in candidates if depths[p] == best_depth)
    return parent


def build_forest(
    nodes: list[FlowNode],
    edges: list[FlowEdge],
    depths: dict[str, int],
    primary_root: str | None,
) -> TreeForest:
    parent = _assign_parents(nodes, edges, depths)
    children: dict[str, list[str]] = {node.id: [] for node in nodes}
    for node_id, parent_id in parent.items():
        if parent_id is not None:
            children[parent_id].append(node_id)
    for node_id in children:
        children[node_id].sort()
    root_ids = [node.id for node in nodes if parent[node.id] is None]
    root_ids.sort(key=lambda nid: (nid != primary_root, depths.get(nid, 0), nid))
    return TreeForest(root_ids, children)

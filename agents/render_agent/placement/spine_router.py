from dataclasses import dataclass

from shared.models.flow_graph import FlowGraph
from placement.flow_reach import reachable_counts


@dataclass(frozen=True)
class SpineResult:
    node_ids: frozenset[str]
    edge_keys: frozenset[tuple[str, str, str]]


class SpineRouter:
    def route(self, graph: FlowGraph) -> SpineResult:
        reach = reachable_counts(graph.nodes, graph.edges)
        out: dict[str, list] = {node.id: [] for node in graph.nodes}
        for edge in graph.edges:
            if edge.kind != "stitch" and edge.source in out:
                out[edge.source].append(edge)
        spine_nodes: set[str] = set()
        spine_edges: set[tuple[str, str, str]] = set()
        for lane in graph.lanes:
            for entry_id in lane.entry_ids:
                self._walk(entry_id, out, reach, spine_nodes, spine_edges)
        for edge in graph.edges:
            edge.is_spine = (edge.source, edge.target, edge.arm_label) in spine_edges
        return SpineResult(frozenset(spine_nodes), frozenset(spine_edges))

    def _walk(
        self,
        entry_id: str,
        out: dict[str, list],
        reach: dict[str, int],
        spine_nodes: set[str],
        spine_edges: set[tuple[str, str, str]],
    ) -> None:
        current = entry_id
        visited: set[str] = set()
        while current in out and current not in visited:
            visited.add(current)
            spine_nodes.add(current)
            candidates = sorted(out[current], key=lambda e: (e.arm_label, e.target))
            if not candidates:
                break
            chosen = max(candidates, key=lambda e: reach.get(e.target, 0))
            spine_edges.add((chosen.source, chosen.target, chosen.arm_label))
            spine_nodes.add(chosen.target)
            current = chosen.target

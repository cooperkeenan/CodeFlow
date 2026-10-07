from itertools import pairwise

from shared.flow_endpoints.slice_graph import SliceGraph
from shared.models.flow_graph import RouteMember


class GroupPaths:
    def build(self, graph: SliceGraph, members: list[RouteMember]) -> list[dict]:
        parents = self._parents(graph)
        direct = {(e.source, e.target) for e in graph.edges}
        ordered = sorted(members, key=lambda m: (m.path, m.method, m.handler_fqn))
        return [
            self._entry(graph, parents, direct, m)
            for m in ordered
            if m.happy is not None and m.happy.node_ids
        ]

    def _entry(
        self,
        graph: SliceGraph,
        parents: dict[str, str],
        direct: set[tuple[str, str]],
        member: RouteMember,
    ) -> dict:
        node_ids = graph.resolve_path(member.happy.node_ids)
        edges: list[list[str]] = []
        missing: list[list[str]] = []
        for pair in pairwise(node_ids):
            target = edges if pair in direct else missing
            if list(pair) not in target:
                target.append(list(pair))
        return {
            "method": member.method,
            "path": member.path,
            "handler_fqn": member.handler_fqn,
            "node_ids": node_ids,
            "edges": edges,
            "reveal": self._reveal(graph, parents, node_ids),
            "ends_in_failure": member.happy.ends_in_failure,
            "missing_edges": missing,
        }

    def _reveal(self, graph: SliceGraph, parents: dict[str, str], node_ids: list[str]) -> list[str]:
        found: set[str] = set()
        for node_id in node_ids:
            current = node_id
            while graph.nodes[current].level > 0 and current in parents:
                current = parents[current]
                if current in found:
                    break
                found.add(current)
        return sorted(found, key=lambda i: (graph.nodes[i].level, i))

    def _parents(self, graph: SliceGraph) -> dict[str, str]:
        parents: dict[str, str] = {}
        for node_id in sorted(graph.nodes):
            for child in graph.nodes[node_id].hidden_children:
                parents.setdefault(child, node_id)
        return parents

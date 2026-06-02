import math

from helpers.module_graph import ModuleGraph

from shared.models.diagram_spec import Archetype


class ArchetypeClassifier:
    def classify(self, graph: ModuleGraph) -> tuple[Archetype, str]:
        n = len(graph.module_names)
        if n == 0:
            return "mesh", "no modules"
        if graph.cycles >= 1:
            return "mesh", f"cycles={graph.cycles}, N={n}"
        connected = [
            name for name in graph.module_names
            if graph.fan_out.get(name, 0) + graph.fan_in.get(name, 0) > 0
        ]
        chain_len = len(graph.longest_path)
        connected_count = len(connected)
        chain_set = set(graph.longest_path)
        chain_covers_connected = (
            len(chain_set & set(connected)) / connected_count if connected_count else 0.0
        )
        max_out = max(graph.fan_out.values(), default=0)
        max_in = max(graph.fan_in.values(), default=0)
        hub_score = max(max_out, max_in)
        hub_threshold = max(2, math.ceil(connected_count / 2)) if connected_count else 2
        if chain_len >= 3 and chain_covers_connected >= 0.7 and hub_score < hub_threshold:
            return (
                "pipeline",
                f"L={chain_len}, connected={connected_count}, coverage={chain_covers_connected:.2f}",
            )
        if hub_score >= hub_threshold:
            return "hub", f"hub_score={hub_score}, connected={connected_count}, threshold={hub_threshold}"
        if graph.zone_uniformity >= 0.7 and n >= 2:
            return "layered", f"zone_uniformity={graph.zone_uniformity:.2f}, N={n}"
        depth = self._depth(graph)
        if max_out >= 2 and depth >= 2:
            return "hierarchy", f"depth={depth}, branching={max_out}, N={n}"
        return "mesh", f"L={chain_len}, N={n}, max_fan_out={max_out}, max_fan_in={max_in}"

    def _depth(self, graph: ModuleGraph) -> int:
        if not graph.topological_order:
            return 0
        depth: dict[str, int] = {n: 0 for n in graph.topological_order}
        for node in graph.topological_order:
            for nxt in graph.adjacency.get(node, set()):
                if depth[node] + 1 > depth[nxt]:
                    depth[nxt] = depth[node] + 1
        return max(depth.values(), default=0)

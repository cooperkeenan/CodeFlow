from collections import deque

from helpers.module_graph import ModuleGraph
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramType


class _TemplateMetaBuilder:
    def build(
        self,
        diagram_type: DiagramType,
        spec: DiagramSpec,
        graph: ModuleGraph,
        pipeline_order: list[str] | None = None,
    ) -> dict:
        if diagram_type == "pipeline":
            base = pipeline_order or graph.topological_order or sorted(graph.module_names)
            return {"module_order": [n for n in base if n in graph.module_names]}
        if diagram_type == "hub_and_spoke":
            hub = max(graph.fan_out, key=graph.fan_out.get) if graph.fan_out else ""
            return {"hub_id": hub}
        if diagram_type == "layered_tier":
            tier_indices: dict[str, int] = {}
            if spec.layout_hint and spec.layout_hint.rank_assignments:
                for ra in spec.layout_hint.rank_assignments:
                    tier_indices[ra.module_name] = ra.rank
            return {"tier_indices": tier_indices}
        if diagram_type == "hierarchy":
            parent_map = {
                n: (sorted(graph.reverse_adjacency[n])[0] if graph.reverse_adjacency.get(n) else None)
                for n in graph.module_names
            }
            return {"parent_map": parent_map, "depth_map": self._depth_map(graph)}
        return {}

    def compute_depth(self, graph: ModuleGraph) -> int:
        dm = self._depth_map(graph)
        return max(dm.values()) if dm else 0

    def _depth_map(self, graph: ModuleGraph) -> dict[str, int]:
        roots = [n for n in graph.module_names if not graph.reverse_adjacency.get(n)]
        if not roots:
            return {n: 0 for n in graph.module_names}
        depth: dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque((r, 0) for r in roots)
        while queue:
            node, d = queue.popleft()
            if node in depth:
                continue
            depth[node] = d
            for child in graph.adjacency.get(node, set()):
                if child not in depth:
                    queue.append((child, d + 1))
        for n in graph.module_names:
            depth.setdefault(n, 0)
        return depth

from collections import deque

from helpers.module_graph import ModuleGraph
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramTemplate, DiagramType, TemplateEdge, TemplateNode


class _TemplateBuilder:
    def build(self, diagram_type: DiagramType, spec: DiagramSpec, graph: ModuleGraph) -> DiagramTemplate:
        nodes = self._build_nodes(diagram_type, spec, graph)
        edges = self._build_edges(spec, graph)
        meta = self._build_meta(diagram_type, spec, graph)
        return DiagramTemplate(type=diagram_type, nodes=nodes, edges=edges, meta=meta)

    def compute_depth(self, graph: ModuleGraph) -> int:
        dm = self._depth_map(graph)
        return max(dm.values()) if dm else 0

    def _build_nodes(
        self, diagram_type: DiagramType, spec: DiagramSpec, graph: ModuleGraph
    ) -> list[TemplateNode]:
        order = self._node_order(diagram_type, spec, graph)
        module_tier: dict[str, str] = {}
        zone_counts: dict[str, int] = {}
        component_counts: dict[str, int] = {}
        for module in spec.modules:
            tier = "secondary"
            for comps in module.zones.values():
                for comp in comps:
                    if comp.tier == "primary":
                        tier = "primary"
                        break
                if tier == "primary":
                    break
            module_tier[module.name] = tier
            zone_counts[module.name] = sum(1 for comps in module.zones.values() if comps)
            component_counts[module.name] = sum(len(comps) for comps in module.zones.values())
        return [
            TemplateNode(
                id=n,
                label=n,
                tier=module_tier.get(n, "secondary"),
                module_name=n,
                zone_count=zone_counts.get(n, 0),
                component_count=component_counts.get(n, 0),
            )
            for n in order
        ]

    def _node_order(
        self, diagram_type: DiagramType, spec: DiagramSpec, graph: ModuleGraph
    ) -> list[str]:
        if diagram_type == "pipeline":
            if spec.layout_hint and spec.layout_hint.module_order:
                base = list(spec.layout_hint.module_order)
                return base + [n for n in graph.module_names if n not in base]
            return graph.topological_order or sorted(graph.module_names)
        if diagram_type == "hub_and_spoke":
            hub = (
                max(graph.fan_out, key=graph.fan_out.get)
                if graph.fan_out
                else (sorted(graph.module_names)[0] if graph.module_names else "")
            )
            return [hub] + sorted(n for n in graph.module_names if n != hub)
        if diagram_type == "layered_tier":
            if spec.layout_hint and spec.layout_hint.rank_assignments:
                ranked = sorted(spec.layout_hint.rank_assignments, key=lambda r: r.rank)
                base = [r.module_name for r in ranked]
                return base + sorted(n for n in graph.module_names if n not in base)
            return graph.topological_order or sorted(graph.module_names)
        if diagram_type == "hierarchy":
            return self._hierarchy_order(graph)
        return sorted(graph.module_names)

    def _hierarchy_order(self, graph: ModuleGraph) -> list[str]:
        roots = sorted(n for n in graph.module_names if not graph.reverse_adjacency.get(n))
        if not roots:
            roots = sorted(graph.module_names[:1])
        order: list[str] = []
        visited: set[str] = set()
        queue: deque[str] = deque(roots)
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            order.append(node)
            for child in sorted(graph.adjacency.get(node, set())):
                queue.append(child)
        return order + sorted(n for n in graph.module_names if n not in visited)

    def _build_edges(self, spec: DiagramSpec, graph: ModuleGraph) -> list[TemplateEdge]:
        comp_to_mod: dict[str, str] = {}
        for module in spec.modules:
            for comps in module.zones.values():
                for comp in comps:
                    comp_to_mod[comp.name] = module.name
        seen: dict[tuple[str, str], str] = {}
        for edge in spec.edges:
            src = comp_to_mod.get(edge.source)
            tgt = comp_to_mod.get(edge.target)
            if src and tgt and src != tgt and (src, tgt) not in seen:
                seen[(src, tgt)] = edge.edge_type
        return [
            TemplateEdge(source=s, target=t, edge_type=et)
            for (s, t), et in sorted(seen.items())
        ]

    def _build_meta(
        self, diagram_type: DiagramType, spec: DiagramSpec, graph: ModuleGraph
    ) -> dict:
        if diagram_type == "pipeline":
            return {"module_order": self._node_order("pipeline", spec, graph)}
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

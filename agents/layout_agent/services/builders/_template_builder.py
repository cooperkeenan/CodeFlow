from collections import deque

from helpers.module_graph import ModuleGraph
from services.builders._module_edge_builder import ModuleEdgeBuilder
from services.builders._template_meta_builder import _TemplateMetaBuilder
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramTemplate, DiagramType, TemplateEdge, TemplateNode


class _TemplateBuilder:
    def __init__(self, meta_builder: _TemplateMetaBuilder, module_edge_builder: ModuleEdgeBuilder) -> None:
        self._meta_builder = meta_builder
        self._module_edge_builder = module_edge_builder

    def build(
        self,
        diagram_type: DiagramType,
        spec: DiagramSpec,
        graph: ModuleGraph,
        pipeline_order: list[str] | None = None,
    ) -> DiagramTemplate:
        nodes = self._build_nodes(diagram_type, spec, graph, pipeline_order)
        edges = self._build_edges(diagram_type, spec, graph, pipeline_order)
        meta = self._meta_builder.build(diagram_type, spec, graph, pipeline_order)
        return DiagramTemplate(type=diagram_type, nodes=nodes, edges=edges, meta=meta)

    def compute_depth(self, graph: ModuleGraph) -> int:
        return self._meta_builder.compute_depth(graph)

    def _build_nodes(
        self,
        diagram_type: DiagramType,
        spec: DiagramSpec,
        graph: ModuleGraph,
        pipeline_order: list[str] | None = None,
    ) -> list[TemplateNode]:
        order = self._node_order(diagram_type, spec, graph, pipeline_order)
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
        self,
        diagram_type: DiagramType,
        spec: DiagramSpec,
        graph: ModuleGraph,
        pipeline_order: list[str] | None = None,
    ) -> list[str]:
        if diagram_type == "pipeline":
            if pipeline_order:
                base = [n for n in pipeline_order if n in graph.module_names]
                return base + sorted(n for n in graph.module_names if n not in set(base))
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

    def _build_edges(
        self,
        diagram_type: DiagramType,
        spec: DiagramSpec,
        graph: ModuleGraph,
        pipeline_order: list[str] | None = None,
    ) -> list[TemplateEdge]:
        if diagram_type == "pipeline":
            base = pipeline_order or self._node_order("pipeline", spec, graph)
            chain = [n for n in base if n in graph.module_names]
            return self._module_edge_builder.pipeline_edges(spec, graph, chain)
        return self._module_edge_builder.real_edges(spec, graph)

from collections import Counter

from helpers.component_archetype_classifier import ComponentArchetypeClassifier
from services.builders._component_view_builder import _ComponentViewBuilder
from services.builders._edge_builder import build_structural as _build_struct_edges
from services.builders._graph_contraction import bfs_depth, contract
from shared.models.diagram_spec import DiagramSpec, Module
from shared.models.diagram_template import DiagramTemplate, TemplateEdge, TemplateNode

_STRUCTURAL = frozenset({"hub_and_spoke", "pipeline", "hierarchy", "layered_tier", "mesh", "dependency_graph"})


class _ViewBuilder:
    def __init__(self, classifier: ComponentArchetypeClassifier) -> None:
        self._classifier = classifier
        self._component_builder = _ComponentViewBuilder(classifier)

    def build_module(
        self, spec: DiagramSpec, module: Module, diagram_type: str, view_set: set[str]
    ) -> DiagramTemplate:
        if diagram_type in _STRUCTURAL:
            return self._build_structural_module(spec, module, diagram_type, view_set)
        nodes: list[TemplateNode] = []
        edges: list[TemplateEdge] = []
        names = {c.name for comps in module.zones.values() for c in comps if not c.nested}
        plan_by_zone = {p.zone: p.clusters for p in (module.cluster_plan or [])}

        for zone_name, comps in module.zones.items():
            if not comps:
                continue
            zone_id = f"zone__{module.name}__{zone_name}"
            nodes.append(TemplateNode(id=zone_id, label=zone_name, tier="primary", module_name=module.name, kind="zone"))
            clusters = plan_by_zone.get(zone_name, [])
            referenced: set[str] = set()
            for cluster in clusters:
                c_id = f"cluster__{module.name}__{zone_name}__{cluster.label}"
                nodes.append(TemplateNode(id=c_id, label=cluster.label, tier="primary",
                                          module_name=module.name, kind="cluster", parent=zone_id, style=cluster.style))
                for m_name in (cluster.members or []):
                    referenced.add(m_name)
                    comp = next((c for cs in module.zones.values() for c in cs if c.name == m_name), None)
                    nodes.append(TemplateNode(
                        id=m_name, label=m_name,
                        tier=comp.tier if comp else "primary",
                        module_name=module.name, kind="component", parent=c_id,
                        drillable=(m_name in view_set),
                    ))
                for child in (cluster.children or []):
                    ch_id = f"cluster__{module.name}__{zone_name}__{cluster.label}__{child.label}"
                    nodes.append(TemplateNode(
                        id=ch_id, label=child.label, tier="primary",
                        module_name=module.name, kind="cluster",
                        parent=c_id, style=child.style,
                    ))
                    for m_name in (child.members or []):
                        referenced.add(m_name)
                        comp = next((c for cs in module.zones.values() for c in cs if c.name == m_name), None)
                        nodes.append(TemplateNode(
                            id=m_name, label=m_name,
                            tier=comp.tier if comp else "primary",
                            module_name=module.name, kind="component", parent=ch_id,
                            drillable=(m_name in view_set),
                        ))
            for comp in comps:
                if not comp.nested and comp.name not in referenced:
                    nodes.append(TemplateNode(
                        id=comp.name, label=comp.name, tier=comp.tier,
                        module_name=module.name, kind="component", parent=zone_id,
                        drillable=(comp.name in view_set),
                    ))
        for e in spec.edges:
            if e.source in names and e.target in names and e.source != e.target:
                edges.append(TemplateEdge(source=e.source, target=e.target, edge_type=e.edge_type))
        return DiagramTemplate(type=diagram_type, nodes=nodes, edges=edges, meta={"module": module.name})

    def _build_structural_module(
        self, spec: DiagramSpec, module: Module, diagram_type: str, view_set: set[str]
    ) -> DiagramTemplate:
        names = {c.name for cs in module.zones.values() for c in cs if not c.nested and c.tier == "primary"}
        intra = [(e.source, e.target) for e in spec.edges
                 if e.source in names and e.target in names and e.source != e.target]
        _roles = {c.name: c.role for cs in module.zones.values() for c in cs if c.name in names}
        cr = contract(names, intra, _roles); names, intra = cr.names, cr.edges
        nodes = [TemplateNode(id=c.name, label=c.name, tier=c.tier, module_name=module.name,
                              kind="component", drillable=(c.name in view_set), description=c.description)
                 for cs in module.zones.values() for c in cs if not c.nested and c.tier == "primary" and c.name in names]
        fan_out: Counter = Counter(s for s, _ in intra)
        hub_id = max(names, key=lambda n: fan_out.get(n, 0)) if names else ""
        depth_map = bfs_depth(hub_id, names, intra)
        edges, struct_order = _build_struct_edges(diagram_type, names, intra)
        meta: dict = {"module": module.name, "hub_id": hub_id, "depth_map": depth_map,
                      **({"order": struct_order} if struct_order else {}), **({"folded": cr.folded} if cr.folded else {})}
        return DiagramTemplate(type=diagram_type, nodes=nodes, edges=edges, meta=meta)

    def build_component(
        self, spec: DiagramSpec, component_name: str, view_set: set[str], comp_types: dict | None = None,
    ) -> DiagramTemplate:
        return self._component_builder.build(spec, component_name, view_set, comp_types)

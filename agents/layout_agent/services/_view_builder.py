from helpers.component_archetype_classifier import ComponentArchetypeClassifier
from shared.models.diagram_spec import DiagramSpec, Module
from shared.models.diagram_template import DiagramTemplate, TemplateEdge, TemplateNode


class _ViewBuilder:
    def __init__(self, classifier: ComponentArchetypeClassifier) -> None:
        self._classifier = classifier

    def build_module(
        self, spec: DiagramSpec, module: Module, diagram_type: str, view_set: set[str]
    ) -> DiagramTemplate:
        nodes: list[TemplateNode] = []
        edges: list[TemplateEdge] = []
        names = {c.name for comps in module.zones.values() for c in comps if not c.nested}
        plan_by_zone = {p.zone: p.clusters for p in (module.cluster_plan or [])}

        for zone_name, comps in module.zones.items():
            if not comps:
                continue
            zone_id = f"zone__{module.name}__{zone_name}"
            nodes.append(TemplateNode(
                id=zone_id, label=zone_name, tier="primary",
                module_name=module.name, kind="zone",
            ))
            clusters = plan_by_zone.get(zone_name, [])
            referenced: set[str] = set()
            for cluster in clusters:
                c_id = f"cluster__{module.name}__{zone_name}__{cluster.label}"
                nodes.append(TemplateNode(
                    id=c_id, label=cluster.label, tier="primary",
                    module_name=module.name, kind="cluster",
                    parent=zone_id, style=cluster.style,
                ))
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

    def build_component(
        self, spec: DiagramSpec, component_name: str, view_set: set[str]
    ) -> DiagramTemplate:
        comp_to_mod = {c.name: m.name for m in spec.modules for cs in m.zones.values() for c in cs}
        all_comps = {c.name: c for m in spec.modules for cs in m.zones.values() for c in cs}
        focused = all_comps.get(component_name)
        if not focused:
            return DiagramTemplate(type="relationship", nodes=[], edges=[], meta={"focus": component_name})
        callers, callees = [], []
        seen_c: set[str] = set()
        seen_e: set[str] = set()
        for e in spec.edges:
            if e.source == e.target or e.edge_type == "import":
                continue
            if e.target == component_name and e.source not in seen_c:
                seen_c.add(e.source); callers.append(e.source)
            if e.source == component_name and e.target not in seen_e:
                seen_e.add(e.target); callees.append(e.target)
        callers, callees = sorted(callers), sorted(callees)
        related = {component_name, *callers, *callees}
        children = sorted(n for n in (focused.children or []) if n in all_comps and n not in related)
        involved = related | set(children)
        diagram_type = self._classifier.classify(component_name, callers, callees, children, all_comps)
        nodes: list[TemplateNode] = []
        for name in [*callers, component_name, *callees, *children]:
            mod = comp_to_mod.get(name, "")
            role = "caller" if name in callers else ("callee" if name in callees else ("child" if name in children else "focus"))
            drillable = name != component_name and name in view_set
            nodes.append(TemplateNode(id=name, label=name, tier="primary", module_name=mod, kind="component", style=role, drillable=drillable))
        edges: list[TemplateEdge] = []
        for e in spec.edges:
            if e.edge_type != "import" and e.source != e.target and e.source in involved and e.target in involved:
                edges.append(TemplateEdge(source=e.source, target=e.target, edge_type=e.edge_type))
        for child in children:
            edges.append(TemplateEdge(source=component_name, target=child, edge_type="call"))
        depth_map = {component_name: 0, **{c: -1 for c in callers}, **{c: 1 for c in callees}, **{c: 1 for c in children}}
        meta = {
            "focus": component_name, "callers": callers, "callees": callees, "children": children,
            "hub_id": component_name, "depth_map": depth_map,
        }
        return DiagramTemplate(type=diagram_type, nodes=nodes, edges=edges, meta=meta)

from collections import Counter

from helpers.component_archetype_classifier import ComponentArchetypeClassifier
from services._container_builder import build_container
from services._edge_builder import build as _build_type_edges, build_structural as _build_struct_edges
from services._graph_contraction import bfs_depth, contract
from shared.models.diagram_spec import DiagramSpec, Module
from shared.models.diagram_template import DiagramTemplate, TemplateEdge, TemplateNode

_STRUCTURAL = frozenset({"hub_and_spoke", "pipeline", "hierarchy", "layered_tier", "mesh", "dependency_graph"})


class _ViewBuilder:
    def __init__(self, classifier: ComponentArchetypeClassifier) -> None:
        self._classifier = classifier

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
                              kind="component", drillable=(c.name in view_set))
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
        folded_map: dict = {}
        if focused.role in {"service", "orchestrator", "repository", "entry"}:
            _s = {*callees, *children}
            _er = [(e.source, e.target) for e in spec.edges if e.source in _s and e.target in _s and e.source != e.target]
            cr = contract(_s, _er, {n: (all_comps[n].role if n in all_comps else "") for n in _s})
            callees = [c for c in callees if c in cr.names]; children = [c for c in children if c in cr.names]
            folded_map = cr.folded
        if folded_map:
            return build_container(component_name, callers, callees, children, folded_map, comp_to_mod, view_set)
        override = (comp_types or {}).get(component_name) or {}
        diagram_type = override.get("type") or self._classifier.classify(component_name, callers, callees, children, all_comps)
        edges, resolved_order = _build_type_edges(diagram_type, component_name, callers, callees, children, override.get("order"), spec)
        step_names = resolved_order if resolved_order is not None else [*callees, *children]
        node_names = [*callers, component_name, *step_names]
        nodes: list[TemplateNode] = []
        seen_n: set[str] = set()
        for name in node_names:
            if name in seen_n:
                continue
            seen_n.add(name)
            mod = comp_to_mod.get(name, "")
            role = "caller" if name in callers else ("callee" if name in callees else ("child" if name in children else "focus"))
            drillable = name != component_name and name in view_set
            nodes.append(TemplateNode(id=name, label=name, tier="primary", module_name=mod, kind="component", style=role, drillable=drillable))
        depth_map = {component_name: 0, **{c: -1 for c in callers}, **{c: 1 for c in callees}, **{c: 1 for c in children}}
        meta: dict = {
            "focus": component_name, "callers": callers, "callees": callees, "children": children,
            "hub_id": component_name, "depth_map": depth_map,
        }
        if resolved_order is not None:
            meta["order"] = resolved_order
        if override.get("reasoning"):
            meta["rationale"] = override["reasoning"]
        return DiagramTemplate(type=diagram_type, nodes=nodes, edges=edges, meta=meta)

from helpers.component_archetype_classifier import ComponentArchetypeClassifier
from services.builders._container_builder import build_container
from services.builders._edge_builder import build as _build_type_edges
from services.builders._graph_contraction import _PRIMARY
from services.builders._neighborhood import contract_steps, wrapping_adapters
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramTemplate, TemplateEdge, TemplateNode

_DRIVER = frozenset({"orchestrator", "entry"})


class _ComponentViewBuilder:
    def __init__(self, classifier: ComponentArchetypeClassifier) -> None:
        self._classifier = classifier

    def build(
        self,
        spec: DiagramSpec,
        component_name: str,
        view_set: set[str],
        comp_types: dict | None = None,
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
                seen_c.add(e.source)
                callers.append(e.source)
            if e.source == component_name and e.target not in seen_e:
                seen_e.add(e.target)
                callees.append(e.target)
        callers, callees = sorted(callers), sorted(callees)
        related = {component_name, *callers, *callees}
        children = sorted(n for n in (focused.children or []) if n in all_comps and n not in related)

        wf = wrapping_adapters(component_name, callers, all_comps, spec.edges)
        if wf.folded and focused.role not in _DRIVER:
            return build_container(
                component_name, wf.pulled_callers, callees, children,
                {component_name: wf.folded}, comp_to_mod, view_set,
            )

        folded_map: dict = {}
        if focused.role in _PRIMARY:
            cs = contract_steps(component_name, callees, children, all_comps, spec.edges)
            callees, children, folded_map = cs.callees, cs.children, cs.folded

        override = (comp_types or {}).get(component_name) or {}
        diagram_type = override.get("type") or self._classifier.classify(
            component_name, callers, callees, children, all_comps, comp_to_mod, spec.edges
        )
        hub_steps = [*callees, *children]
        if diagram_type == "hub_and_spoke" and not self._classifier.is_api_hub(component_name, hub_steps, comp_to_mod, spec.edges):
            diagram_type = "hierarchy" if len(hub_steps) >= 3 else "relationship"
        edges, resolved_order = _build_type_edges(
            diagram_type, component_name, callers, callees, children, override.get("order"), spec
        )

        if folded_map:
            connected = {e.target for e in edges if e.source == component_name}
            edges += [
                TemplateEdge(source=component_name, target=s, edge_type="call")
                for s in folded_map if s not in connected
            ]

        step_names = resolved_order if resolved_order is not None else [*callees, *children]
        node_names = [*callers, component_name, *step_names]
        present = set(node_names)
        inline_children: list[str] = []
        for step in step_names:
            s_comp = all_comps.get(step)
            s_deps = set(s_comp.children or []) if s_comp else set()
            for e in spec.edges:
                if e.edge_type != "import" and e.source == step and e.target != step:
                    s_deps.add(e.target)
            s_deps = {d for d in s_deps if d in all_comps}
            if len(s_deps) == 1:
                child = next(iter(s_deps))
                if child not in present and child != component_name:
                    present.add(child)
                    inline_children.append(child)
                    edges.append(TemplateEdge(source=step, target=child, edge_type="call"))
        node_names = [*node_names, *inline_children]
        nodes: list[TemplateNode] = []
        seen_n: set[str] = set()
        for name in node_names:
            if name in seen_n:
                continue
            seen_n.add(name)
            mod = comp_to_mod.get(name, "")
            role = "caller" if name in callers else (
                "callee" if name in callees else ("child" if name in children else "focus")
            )
            drillable = name != component_name and name in view_set
            comp_desc = all_comps[name].description if name in all_comps else ""
            nodes.append(TemplateNode(
                id=name, label=name,
                tier=all_comps[name].tier if name in all_comps else "primary",
                module_name=mod,
                kind="component", style=role, drillable=drillable, description=comp_desc,
            ))
        depth_map = {
            component_name: 0,
            **{c: -1 for c in callers},
            **{c: 1 for c in callees},
            **{c: 1 for c in children},
            **{c: 2 for c in inline_children},
        }
        meta: dict = {
            "focus": component_name, "callers": callers, "callees": callees, "children": children,
            "hub_id": component_name, "depth_map": depth_map,
        }
        if resolved_order is not None:
            meta["order"] = resolved_order
        if override.get("reasoning"):
            meta["rationale"] = override["reasoning"]
        if folded_map:
            meta["folded"] = folded_map
        return DiagramTemplate(type=diagram_type, nodes=nodes, edges=edges, meta=meta)

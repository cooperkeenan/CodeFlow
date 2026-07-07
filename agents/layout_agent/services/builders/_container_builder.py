from shared.models.diagram_template import DiagramTemplate, TemplateEdge, TemplateNode


def build_container(
    focus: str,
    callers: list[str],
    callees: list[str],
    children: list[str],
    folded: dict[str, list[str]],
    comp_to_mod: dict[str, str],
    view_set: set[str],
) -> DiagramTemplate:
    ctr_id = f"container__{focus}"
    mod = comp_to_mod.get(focus, "")
    nodes: list[TemplateNode] = []
    for c in callers:
        nodes.append(TemplateNode(id=c, label=c, tier="primary", module_name=comp_to_mod.get(c, ""),
                                  kind="component", style="caller", drillable=(c in view_set)))
    nodes.append(TemplateNode(id=ctr_id, label=focus, tier="primary", module_name=mod, kind="cluster"))
    for a in folded.get(focus, []):
        nodes.append(TemplateNode(id=a, label=a, tier="primary", module_name=mod,
                                  kind="component", parent=ctr_id))
    nodes.append(TemplateNode(id=focus, label=focus, tier="primary", module_name=mod,
                              kind="component", parent=ctr_id, style="focus"))
    for ch in children:
        nodes.append(TemplateNode(id=ch, label=ch, tier="primary", module_name=comp_to_mod.get(ch, mod),
                                  kind="component", parent=ctr_id, drillable=(ch in view_set)))
    edges: list[TemplateEdge] = [TemplateEdge(source=c, target=focus, edge_type="call") for c in callers]
    for a in folded.get(focus, []):
        edges.append(TemplateEdge(source=a, target=focus, edge_type="sequence"))
    for ch in children:
        edges.append(TemplateEdge(source=focus, target=ch, edge_type="call"))
    return DiagramTemplate(
        type="container", nodes=nodes, edges=edges,
        meta={"focus": focus, "callers": callers, "container": ctr_id, "folded": folded},
    )

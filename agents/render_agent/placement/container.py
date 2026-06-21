from shared.models.diagram_template import DiagramTemplate

NODE_W, NODE_H = 180, 58
H_GAP = 40
H_PAD = 20
V_PAD = 16
HEAD = 28
CALLER_MARGIN = 120


def place_component_container(template: DiagramTemplate) -> list[dict]:
    ctr_node = next((n for n in template.nodes if n.kind == "cluster"), None)
    if not ctr_node:
        return []

    callers = [n for n in template.nodes if n.parent is None and n.id != ctr_node.id]
    members = [n for n in template.nodes if n.parent == ctr_node.id]

    content_w = len(members) * NODE_W + max(0, len(members) - 1) * H_GAP
    ctr_w = content_w + 2 * H_PAD
    ctr_h = HEAD + V_PAD + NODE_H + V_PAD

    caller_h = len(callers) * NODE_H + max(0, len(callers) - 1) * V_PAD
    caller_y_start = (ctr_h - caller_h) // 2

    result: list[dict] = []
    ctr_x = CALLER_MARGIN + H_GAP if callers else 0
    result.append({
        "id": ctr_node.id,
        "type": "clusterGroup",
        "selectable": False,
        "draggable": False,
        "position": {"x": ctr_x, "y": 0},
        "style": {"width": ctr_w, "height": ctr_h},
        "data": {"label": ctr_node.label, "module": ctr_node.module_name},
    })

    mx = H_PAD
    for m in members:
        result.append({
            "id": m.id,
            "type": "custom",
            "parentNode": ctr_node.id,
            "extent": "parent",
            "position": {"x": mx, "y": HEAD + V_PAD},
            "data": {"label": m.label, "module": m.module_name, "drillable": m.drillable, "tier": m.tier},
        })
        mx += NODE_W + H_GAP

    for i, caller in enumerate(callers):
        result.append({
            "id": caller.id,
            "type": "custom",
            "position": {"x": 0, "y": caller_y_start + i * (NODE_H + V_PAD)},
            "data": {
                "label": caller.label, "module": caller.module_name,
                "drillable": caller.drillable, "tier": caller.tier,
            },
        })

    return result

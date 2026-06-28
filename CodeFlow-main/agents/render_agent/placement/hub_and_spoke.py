import math

from shared.models.diagram_template import DiagramTemplate


def place(template: DiagramTemplate) -> list[dict]:
    if not template.nodes:
        return []
    hub_id = template.meta.get("hub_id", template.nodes[0].module_name)
    hub_nodes = [n for n in template.nodes if n.module_name == hub_id]
    spokes = [n for n in template.nodes if n.module_name != hub_id]
    if not hub_nodes:
        hub_nodes, spokes = [template.nodes[0]], template.nodes[1:]

    hub = hub_nodes[0]
    n = len(spokes) or 1
    radius = max(260, len(spokes) * 65)

    result = [
        {
            "id": f"mod__{hub.module_name}",
            "type": "moduleSummary",
            "position": {"x": 0, "y": 0},
            "data": {"label": hub.label, "moduleName": hub.module_name, "drillable": True},
        }
    ]
    for i, node in enumerate(spokes):
        angle = (i / n) * 2 * math.pi - math.pi / 2
        result.append({
            "id": f"mod__{node.module_name}",
            "type": "moduleSummary",
            "position": {"x": round(math.cos(angle) * radius), "y": round(math.sin(angle) * radius)},
            "data": {"label": node.label, "moduleName": node.module_name, "drillable": True},
        })
    return result


def place_component(template: DiagramTemplate) -> list[dict]:
    if not template.nodes:
        return []
    hub_id = template.meta.get("hub_id", template.nodes[0].id)
    hub_nodes = [n for n in template.nodes if n.id == hub_id]
    spokes = [n for n in template.nodes if n.id != hub_id]
    if not hub_nodes:
        hub_nodes, spokes = [template.nodes[0]], template.nodes[1:]

    hub = hub_nodes[0]
    n = len(spokes) or 1
    radius = max(260, len(spokes) * 65)

    result = [
        {
            "id": hub.id, "type": "custom",
            "position": {"x": 0, "y": 0},
            "data": {"label": hub.label, "module": hub.module_name, "isEntry": True, "drillable": hub.drillable, "tier": hub.tier},
        }
    ]
    for i, node in enumerate(spokes):
        angle = (i / n) * 2 * math.pi - math.pi / 2
        result.append({
            "id": node.id, "type": "custom",
            "position": {"x": round(math.cos(angle) * radius), "y": round(math.sin(angle) * radius)},
            "data": {"label": node.label, "module": node.module_name, "isEntry": False, "drillable": node.drillable, "tier": node.tier},
        })
    return result

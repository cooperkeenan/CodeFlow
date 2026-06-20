from shared.models.diagram_template import DiagramTemplate

_MOD_W = 240
_MOD_H = 110
_MOD_GAP_X = 110
_MOD_GAP_Y = 130
_NODE_W = 180
_NODE_H = 58
_NODE_GAP_X = 100
_NODE_GAP_Y = 80


def place(template: DiagramTemplate) -> list[dict]:
    depth_map: dict[str, int] = template.meta.get("depth_map", {})
    by_depth: dict[int, list] = {}
    for node in template.nodes:
        depth = depth_map.get(node.module_name, 0)
        by_depth.setdefault(depth, []).append(node)

    result = []
    for row_idx, depth in enumerate(sorted(by_depth)):
        row = by_depth[depth]
        row_w = len(row) * _MOD_W + (len(row) - 1) * _MOD_GAP_X
        for i, node in enumerate(row):
            x = round(i * (_MOD_W + _MOD_GAP_X) - row_w / 2 + _MOD_W / 2)
            y = row_idx * (_MOD_H + _MOD_GAP_Y)
            result.append({
                "id": f"mod__{node.module_name}",
                "type": "moduleSummary",
                "position": {"x": x, "y": y},
                "data": {"label": node.label, "moduleName": node.module_name, "drillable": True},
            })
    return result


def place_component(template: DiagramTemplate) -> list[dict]:
    depth_map: dict[str, int] = template.meta.get("depth_map", {})
    by_depth: dict[int, list] = {}
    for node in template.nodes:
        depth = depth_map.get(node.id, 0)
        by_depth.setdefault(depth, []).append(node)

    result = []
    for row_idx, depth in enumerate(sorted(by_depth)):
        row = by_depth[depth]
        row_w = len(row) * _NODE_W + (len(row) - 1) * _NODE_GAP_X
        for i, node in enumerate(row):
            x = round(i * (_NODE_W + _NODE_GAP_X) - row_w / 2 + _NODE_W / 2)
            y = row_idx * (_NODE_H + _NODE_GAP_Y)
            result.append({
                "id": node.id, "type": "custom",
                "position": {"x": x, "y": y},
                "data": {"label": node.label, "module": node.module_name, "isEntry": node.style == "focus", "drillable": node.drillable, "tier": node.tier},
            })
    return result

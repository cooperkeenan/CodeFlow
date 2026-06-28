from shared.models.diagram_template import DiagramTemplate

_NODE_W = 180
_NODE_H = 58
_COL_GAP = 100
_ROW_GAP = 28


def place(template: DiagramTemplate) -> list[dict]:
    meta = template.meta
    focus = meta.get("focus", "")
    callers: list[str] = meta.get("callers", [])
    callees: list[str] = meta.get("callees", [])
    children: list[str] = meta.get("children", [])

    col_w = _NODE_W + _COL_GAP
    row_h = _NODE_H + _ROW_GAP
    caller_h = max(1, len(callers)) * row_h
    callee_h = max(1, len(callees)) * row_h
    band_h = max(caller_h, callee_h, row_h)

    by_id = {n.id: n for n in template.nodes}
    nodes: list[dict] = []

    for i, name in enumerate(callers):
        n = by_id.get(name)
        nodes.append(_comp_node(name, n, {"x": 0, "y": round((band_h - caller_h) / 2 + i * row_h)},
                                drillable=n.drillable if n else False))

    nodes.append(_comp_node(focus, by_id.get(focus),
                            {"x": col_w, "y": round((band_h - row_h) / 2)}, is_entry=True, drillable=False))

    for i, name in enumerate(callees):
        n = by_id.get(name)
        nodes.append(_comp_node(name, n, {"x": 2 * col_w, "y": round((band_h - callee_h) / 2 + i * row_h)},
                                drillable=n.drillable if n else False))

    for i, name in enumerate(children):
        n = by_id.get(name)
        nodes.append(_comp_node(name, n, {"x": col_w, "y": band_h + _ROW_GAP + i * row_h},
                                drillable=n.drillable if n else False))

    return nodes


def _comp_node(name: str, node, pos: dict, is_entry: bool = False, drillable: bool = False) -> dict:
    module_name = node.module_name if node else ""
    return {
        "id": name, "type": "custom",
        "position": pos,
        "data": {"label": name, "module": module_name, "isEntry": is_entry, "drillable": drillable},
    }

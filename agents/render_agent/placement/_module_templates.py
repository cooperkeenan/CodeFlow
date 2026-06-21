NODE_W = 180
NODE_H = 58
CX = 24
CY = 20
HUB_GAP = 90
PER_ROW = 3


def _chunk(lst: list, size: int) -> list:
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def _grid(members: list[str]) -> dict:
    rows = _chunk(members, PER_ROW)
    content_w = max((NODE_W, *(len(r) * NODE_W + (len(r) - 1) * CX for r in rows))) if rows else NODE_W
    placed, y = [], 0
    for row in rows:
        row_w = len(row) * NODE_W + (len(row) - 1) * CX
        x = (content_w - row_w) / 2
        for name in row:
            placed.append({"name": name, "x": round(x), "y": y})
            x += NODE_W + CX
        y += NODE_H + CY
    h = len(rows) * NODE_H + max(0, len(rows) - 1) * CY if rows else 0
    return {"width": content_w, "height": h, "placed": placed, "edges": []}


def _stack(members: list[str]) -> dict:
    placed = [{"name": m, "x": 0, "y": i * (NODE_H + CY)} for i, m in enumerate(members)]
    h = len(members) * NODE_H + max(0, len(members) - 1) * CY if members else 0
    return {"width": NODE_W, "height": h, "placed": placed, "edges": []}


def _pipeline(members: list[str]) -> dict:
    base = _stack(members)
    edges = [{"source": members[i], "target": members[i + 1]} for i in range(len(members) - 1)]
    return {**base, "edges": edges}


def _hierarchy(members: list[str]) -> dict:
    if len(members) < 2:
        return _grid(members)
    root, children = members[0], members[1:]
    vgap = CY * 2
    block = _grid(children)
    width = max(NODE_W, block["width"])
    x_off = (width - block["width"]) / 2
    placed = [{"name": root, "x": round((width - NODE_W) / 2), "y": 0}]
    for p in block["placed"]:
        placed.append({"name": p["name"], "x": round(p["x"] + x_off), "y": p["y"] + NODE_H + vgap})
    return {
        "width": width,
        "height": NODE_H + vgap + block["height"],
        "placed": placed,
        "edges": [{"source": root, "target": c} for c in children],
    }


def _hub(members: list[str]) -> dict:
    if len(members) < 2:
        return _grid(members)
    hub, spokes = members[0], members[1:]
    spokes_h = len(spokes) * NODE_H + max(0, len(spokes) - 1) * CY
    col_x = NODE_W + HUB_GAP
    placed = [{"name": hub, "x": 0, "y": round(max(0, (spokes_h - NODE_H) / 2))}]
    for i, s in enumerate(spokes):
        placed.append({"name": s, "x": col_x, "y": i * (NODE_H + CY)})
    return {
        "width": col_x + NODE_W,
        "height": max(NODE_H, spokes_h),
        "placed": placed,
        "edges": [{"source": hub, "target": s} for s in spokes],
    }


_STYLES: dict = {"grid": _grid, "stack": _stack, "pipeline": _pipeline, "hierarchy": _hierarchy, "hub": _hub}


def apply_style(style: str | None, members: list[str]) -> dict:
    return _STYLES.get(style or "grid", _grid)(members)

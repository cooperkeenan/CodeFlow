from shared.models.diagram_template import DiagramTemplate

NODE_W = 180
NODE_H = 84
COL_GAP = 100
ROW_GAP = 28


def place_component(template: DiagramTemplate) -> list[dict]:
    if not template.nodes:
        return []

    focus = template.meta.get("focus", "")
    node_ids = {n.id for n in template.nodes}
    if not focus or focus not in node_ids:
        focus = template.nodes[0].id

    rank: dict[str, int | None] = {n.id: None for n in template.nodes}
    rank[focus] = 0

    changed = True
    for _ in range(len(template.nodes)):
        if not changed:
            break
        changed = False
        for edge in template.edges:
            s, t = edge.source, edge.target
            s_r = rank.get(s)
            t_r = rank.get(t)
            if s_r is not None:
                new_t = s_r + 1
                if t_r is None or t_r < new_t:
                    rank[t] = new_t
                    changed = True
            if t_r is not None:
                new_s = t_r - 1
                if s_r is None or s_r > new_s:
                    rank[s] = new_s
                    changed = True

    for node in template.nodes:
        if rank[node.id] is None:
            rank[node.id] = 0

    by_rank: dict[int, list] = {}
    for node in template.nodes:
        r = rank[node.id]
        if r is not None:
            by_rank.setdefault(r, []).append(node)

    min_rank = min(by_rank)
    col_step = NODE_W + COL_GAP
    row_step = NODE_H + ROW_GAP
    result: list[dict] = []

    for r, col_nodes in by_rank.items():
        x = (r - min_rank) * col_step
        k = len(col_nodes)
        for i, node in enumerate(sorted(col_nodes, key=lambda n: n.id)):
            y = round(i * row_step - (k - 1) * row_step / 2)
            result.append({
                "id": node.id,
                "type": "custom",
                "position": {"x": x, "y": y},
                "data": {
                    "label": node.label,
                    "module": node.module_name,
                    "isEntry": node.id == focus,
                    "drillable": node.drillable,
                    "tier": node.tier,
                },
            })

    return result

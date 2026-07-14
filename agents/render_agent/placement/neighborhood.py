from shared.models.diagram_template import DiagramTemplate, TemplateNode

NODE_W = 180
NODE_H = 84
COL_GAP = 100
ROW_GAP = 28


def _compute_ranks(template: DiagramTemplate, focus: str) -> dict[str, int]:
    rank: dict[str, int | None] = {n.id: None for n in template.nodes}
    rank[focus] = 0
    changed = True
    for _ in range(len(template.nodes)):
        if not changed:
            break
        changed = False
        for edge in template.edges:
            s, t = edge.source, edge.target
            s_r, t_r = rank.get(s), rank.get(t)
            if s_r is not None and (t_r is None or t_r < s_r + 1):
                rank[t] = s_r + 1
                changed = True
            if t_r is not None and (s_r is None or s_r > t_r - 1):
                rank[s] = t_r - 1
                changed = True
    for node in template.nodes:
        if rank[node.id] is None:
            rank[node.id] = 0
    return rank  # type: ignore[return-value]


def _node_dict(node: TemplateNode, x: int, y: int, focus: str) -> dict:
    return {
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
    }


def _original_layout(
    template: DiagramTemplate, rank: dict[str, int], focus: str
) -> list[dict]:
    by_rank: dict[int, list] = {}
    for node in template.nodes:
        by_rank.setdefault(rank[node.id], []).append(node)
    min_rank = min(by_rank)
    col_step, row_step = NODE_W + COL_GAP, NODE_H + ROW_GAP
    result: list[dict] = []
    for r, col_nodes in by_rank.items():
        x = (r - min_rank) * col_step
        k = len(col_nodes)
        for i, node in enumerate(sorted(col_nodes, key=lambda n: n.id)):
            y = round(i * row_step - (k - 1) * row_step / 2)
            result.append(_node_dict(node, x, y, focus))
    return result


def _anchor_for(
    node_id: str, spine: set[str], rank: dict[str, int],
    template: DiagramTemplate, focus: str,
) -> str:
    candidates = [e.source for e in template.edges if e.target == node_id and e.source in spine]
    if candidates:
        return max(candidates, key=lambda s: rank[s])
    lower = [s for s in spine if rank[s] <= rank[node_id]]
    return max(lower, key=lambda s: rank[s]) if lower else focus


def place_component(template: DiagramTemplate) -> list[dict]:
    if not template.nodes:
        return []
    focus = template.meta.get("focus", "")
    node_ids = {n.id for n in template.nodes}
    if not focus or focus not in node_ids:
        focus = template.nodes[0].id

    rank = _compute_ranks(template, focus)
    spine = {focus} | {n.id for n in template.nodes if n.tier == "primary"}
    secondary = {n.id for n in template.nodes if n.id not in spine}

    if not secondary:
        return _original_layout(template, rank, focus)

    spine_ranks = sorted({rank[s] for s in spine})
    col_index = {r: i for i, r in enumerate(spine_ranks)}
    col_step, row_step = NODE_W + COL_GAP, NODE_H + ROW_GAP
    nodes_by_id = {n.id: n for n in template.nodes}

    spine_by_col: dict[int, list[str]] = {}
    for s in spine:
        spine_by_col.setdefault(col_index[rank[s]], []).append(s)

    result: list[dict] = []
    spine_bottom: dict[int, int] = {}
    for ci, members in spine_by_col.items():
        x = ci * col_step
        k = len(members)
        for i, sid in enumerate(sorted(members)):
            y = round(i * row_step - (k - 1) * row_step / 2)
            result.append(_node_dict(nodes_by_id[sid], x, y, focus))
            spine_bottom[ci] = max(spine_bottom.get(ci, 0), y)

    branch_by_col: dict[int, list[str]] = {}
    for sec_id in secondary:
        anchor = _anchor_for(sec_id, spine, rank, template, focus)
        ci = col_index.get(rank[anchor])
        if ci is None:
            ci = col_index.get(min(spine_ranks, key=lambda r: abs(r - rank[anchor])), 0)
        branch_by_col.setdefault(ci, []).append(sec_id)

    for ci, members in branch_by_col.items():
        x = ci * col_step
        base_y = spine_bottom.get(ci, 0) + row_step
        for i, sec_id in enumerate(sorted(members)):
            result.append(_node_dict(nodes_by_id[sec_id], x, base_y + i * row_step, focus))

    return result

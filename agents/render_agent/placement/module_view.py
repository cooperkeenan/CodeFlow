from collections import defaultdict

from placement._module_templates import apply_style
from shared.models.diagram_template import DiagramTemplate, TemplateNode

ZPADX, ZPADY, ZHEAD, ZGAP = 14, 12, 22, 14
MPAD, MHEAD = 16, 32
CPADX, CPADY, CHEAD, CGAP = 12, 10, 20, 22
CLUSTERS_PER_ROW = 3
NODE_W, NODE_H = 180, 58


def place(template: DiagramTemplate) -> list[dict]:
    module_name = template.meta.get("module", "module")
    mod_id = f"mod__{module_name}"
    by_id = {n.id: n for n in template.nodes}
    ch: dict[str | None, list[TemplateNode]] = defaultdict(list)
    for n in template.nodes:
        ch[n.parent].append(n)

    result: list[dict] = []
    zy, inner_w = MHEAD, 0
    zone_placements = []

    for zone_node in ch.get(None, []):
        if zone_node.kind != "zone":
            continue
        zone_id = zone_node.id
        cluster_nodes = [n for n in ch.get(zone_id, []) if n.kind == "cluster"]
        bare_comps = [n for n in ch.get(zone_id, []) if n.kind == "component"]

        descs: list[tuple[TemplateNode, dict]] = []
        for cn in cluster_nodes:
            descs.append((cn, _layout_cluster(cn, ch)))
        if bare_comps:
            virtual = TemplateNode(id="__flat__", label="", tier="primary", module_name=module_name, kind="cluster", style="grid")
            descs.append((virtual, _layout_cluster(virtual, {virtual.id: bare_comps})))

        rows = [descs[i:i + CLUSTERS_PER_ROW] for i in range(0, len(descs), CLUSTERS_PER_ROW)]
        content_w = max((sum(d["bw"] for _, d in row) + max(0, len(row) - 1) * CGAP for row in rows), default=NODE_W)
        zone_w = content_w + 2 * ZPADX
        inner_w = max(inner_w, zone_w)

        cluster_abs, cy = [], ZHEAD + ZPADY
        for row in rows:
            row_h = max((d["bh"] for _, d in row), default=0)
            cx = ZPADX
            for cn, desc in row:
                cluster_abs.append((cn, desc, cx, cy))
                cx += desc["bw"] + CGAP
            cy += row_h + CGAP

        zone_h = cy - CGAP + ZPADY
        zone_placements.append((zone_node, zone_id, zone_w, zone_h, zy, cluster_abs))
        zy += zone_h + ZGAP

    mod_w, mod_h = inner_w + 2 * MPAD, zy - ZGAP + MPAD
    result.append({"id": mod_id, "type": "moduleGroup", "selectable": False, "draggable": False,
                   "position": {"x": 0, "y": 0}, "style": {"width": mod_w, "height": mod_h, "zIndex": -2},
                   "data": {"label": module_name, "module": module_name}})

    for zone_node, zone_id, zone_w, zone_h, zone_y, cluster_abs in zone_placements:
        result.append({"id": zone_id, "type": "zoneGroup", "selectable": False, "draggable": False,
                       "parentNode": mod_id, "extent": "parent",
                       "position": {"x": MPAD, "y": zone_y},
                       "style": {"width": zone_w, "height": zone_h, "zIndex": -1},
                       "data": {"label": zone_node.label, "module": module_name}})
        for cn, desc, cx, cy in cluster_abs:
            if cn.id != "__flat__":
                result.append({"id": cn.id, "type": "clusterGroup", "selectable": False, "draggable": False,
                               "parentNode": zone_id, "extent": "parent",
                               "position": {"x": cx, "y": cy},
                               "style": {"width": desc["bw"], "height": desc["bh"]},
                               "data": {"label": cn.label, "module": module_name}})
                parent_id = cn.id
            else:
                parent_id = zone_id
            for p in desc["placed"]:
                result.append({"id": p["name"], "type": "custom",
                               "parentNode": parent_id, "extent": "parent",
                               "position": {"x": p["x"] + CPADX, "y": p["y"] + CHEAD + CPADY},
                               "data": {"label": p["name"], "module": module_name,
                                        "zone": zone_node.label,
                                        "drillable": by_id[p["name"]].drillable if p["name"] in by_id else False,
                                        "tier": by_id.get(p["name"], cn).tier if p["name"] in by_id else "primary"}})
    return result


def _layout_cluster(cn: TemplateNode, ch: dict) -> dict:
    members = _all_components(cn.id, ch)
    tpl = apply_style(cn.style, members)
    inner_w = max(NODE_W, tpl["width"])
    bh = CHEAD + CPADY + (tpl["height"] or 0) + CPADY if members else CHEAD + 2 * CPADY
    return {"bw": inner_w + 2 * CPADX, "bh": bh, "placed": tpl["placed"], "edges": tpl["edges"]}


def _all_components(node_id: str, ch: dict) -> list[str]:
    result: list[str] = []
    for n in ch.get(node_id, []):
        if n.kind == "component":
            result.append(n.id)
        elif n.kind == "cluster":
            result.extend(_all_components(n.id, ch))
    return result

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from happy_path_rules import (
    MAX_LEAF_ROUTES,
    find_path,
    is_dag,
    route_failures,
    twin_failures,
    visible_count,
)

from shared.flow_endpoints.endpoint_group import GroupForest
from shared.flow_endpoints.factory import (
    build_group_overview,
    build_group_subgraph,
    build_group_tree,
)
from shared.flow_endpoints.terminal_closer import LINK_PREFIX
from shared.models.flow_graph import FlowGraph, FlowNode, RouteMember


def _load(out_dir: Path) -> FlowGraph:
    return FlowGraph.model_validate(json.loads((out_dir / "flow_graph.json").read_text("utf-8")))


def _entries(graph: FlowGraph) -> list[FlowNode]:
    return sorted(
        (n for n in graph.nodes
         if n.kind == "entry" and n.members and not n.id.startswith("entry:seed:")),
        key=lambda n: n.id,
    )


def _snapshot(graph: FlowGraph) -> str:
    forest = build_group_tree().build(graph)
    subgraph, overview = build_group_subgraph(), build_group_overview()
    parts = [json.dumps([[g.id, g.entry_id, len(g.routes)] for g in forest.groups])]
    for g in forest.groups:
        view = subgraph.slice(graph, forest, g.id) or overview.slice(graph, forest, g.id)
        parts.append(view.model_dump_json() if view else "null")
    return "\n".join(parts)


def _row(leaf_id: str, member: RouteMember, view: FlowGraph | None, reasons: list[str]) -> str:
    entry = (find_path(view, member) or [{}])[0] if view else {}
    ids = entry.get("node_ids") or []
    nodes = {n.id: n for n in view.nodes} if view else {}
    last = nodes[ids[-1]].label if ids and ids[-1] in nodes else "-"
    before = view.meta.get("visible_before_promote", "-") if view else "-"
    after = visible_count(view) if view else "-"
    verdict = "OK" if not reasons else "FAIL(" + "; ".join(reasons) + ")"
    return (
        f"{leaf_id} | {member.handler_fqn.rsplit('.', 1)[-1]} | {member.method} {member.path} | "
        f"{len(ids)} | {len(entry.get('reveal') or [])} | {before} | {after} | "
        f"{bool(entry.get('ends_in_failure'))} | {last} | {verdict}"
    )


def _overview_failures(graph: FlowGraph, forest: GroupForest) -> list[str]:
    overview = build_group_overview()
    out: list[str] = []
    for group in forest.groups:
        if group.is_leaf:
            continue
        view = overview.slice(graph, forest, group.id)
        ids = {n.id for n in view.nodes} if view else set()
        out.extend(
            f"overview {group.id} lacks {LINK_PREFIX}{c}"
            for c in group.children if f"{LINK_PREFIX}{c}" not in ids
        )
    return out


def main() -> int:
    graph = _load(Path(sys.argv[1]))
    known = {n.id for n in graph.nodes}
    forest = build_group_tree().build(graph)
    subgraph = build_group_subgraph()
    cache: dict[str, FlowGraph | None] = {}
    stats: dict[str, dict] = {}
    global_fail: list[str] = []
    total = failures = 0
    print("leaf | handler | route | path len | reveal len | before | after | ends_in_failure | last | verdict")
    for entry in _entries(graph):
        views: dict[str, FlowGraph | None] = {}
        for m in entry.members:
            leaf = forest.leaf_of(entry.id, m.handler_fqn, m.method, m.path)
            if leaf is None:
                global_fail.append(f"{m.method} {m.path} in no leaf")
                continue
            if leaf.id not in cache:
                cache[leaf.id] = subgraph.slice(graph, forest, leaf.id)
            views[leaf.id] = cache[leaf.id]
            reasons = route_failures(cache[leaf.id], m, entry.id, known)
            twins = twin_failures(entry.members, cache[leaf.id])
            if (m.method, m.path, m.handler_fqn) in twins:
                reasons.append(twins[(m.method, m.path, m.handler_fqn)])
            print(_row(leaf.id, m, cache[leaf.id], reasons))
            total += 1
            failures += bool(reasons)
    for leaf in forest.leaves():
        view = cache.get(leaf.id)
        reveals = [len(p["reveal"]) for p in (view.meta.get("paths") if view else None) or []]
        stats[leaf.id] = {"routes": leaf.route_count, "overflow": leaf.overflow, "view": view,
                          "reveal": max(reveals, default=0)}
        if view is not None and not is_dag(view):
            global_fail.append(f"leaf {leaf.id} edges are not a DAG")
        if leaf.route_count > MAX_LEAF_ROUTES and not leaf.overflow:
            global_fail.append(f"leaf {leaf.id} has {leaf.route_count} routes without overflow")
    seen = [r for g in forest.leaves() for r in g.routes]
    if len(seen) != len(set(seen)) or len(seen) != sum(len(e.members) for e in _entries(graph)):
        global_fail.append("routes are not in exactly one leaf each")
    global_fail.extend(_overview_failures(graph, forest))
    if _snapshot(graph) != _snapshot(graph):
        global_fail.append("forest/views are not deterministic")
    print("\nleaf | routes | overflow | visible before | visible after | max reveal")
    for leaf_id, s in sorted(stats.items()):
        view = s["view"]
        before = view.meta.get("visible_before_promote") if view else "-"
        after = visible_count(view) if view else "-"
        print(f"{leaf_id} | {s['routes']} | {s['overflow']} | {before} | {after} | {s['reveal']}")
    for reason in global_fail:
        print(f"GLOBAL FAIL: {reason}")
    print(f"\nroutes={total} failures={failures} global_failures={len(global_fail)} leaves={len(stats)}")
    return 1 if failures or global_fail or total == 0 else 0


if __name__ == "__main__":
    sys.exit(main())

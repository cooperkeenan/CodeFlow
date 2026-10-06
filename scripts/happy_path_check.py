import itertools
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from shared.flow_endpoints.endpoint_elider import DEFAULT_BUDGET
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.flow_endpoints.factory import build_route_subgraph
from shared.models.flow_graph import FlowGraph, FlowNode, RouteMember


def _visible(view: FlowGraph) -> int:
    return sum(1 for n in view.nodes if n.level == 0)


def _payload_failures(
    view: FlowGraph, entry_id: str, nodes: dict[str, FlowNode]
) -> list[str]:
    payload = view.meta.get("happy") or {}
    ids: list[str] = payload.get("node_ids") or []
    if not ids:
        return ["payload empty"]
    out: list[str] = []
    if ids[0] != entry_id:
        out.append("payload first is not entry")
    if len(set(ids)) != len(ids):
        out.append("payload has duplicates")
    for node_id in ids:
        node = nodes.get(node_id)
        if node is None:
            out.append(f"payload node {node_id} missing from slice")
        elif node.level != 0:
            out.append(f"payload node {node_id} not visible")
    direct = {(e.source, e.target) for e in view.edges}
    listed = {tuple(e) for e in payload.get("edges") or []}
    for pair in itertools.pairwise(ids):
        if pair not in direct:
            out.append(f"no direct edge {pair[0]} -> {pair[1]}")
        if pair not in listed:
            out.append(f"edge {pair[0]} -> {pair[1]} not in payload edges")
    last = nodes.get(ids[-1])
    terminal = last is not None and (last.kind == "outcome" or last.effect_kind == "response")
    if last is not None and not terminal and not payload.get("ends_in_failure"):
        out.append(f"path ends on {last.kind} {ids[-1]}")
    return out


def _route_failures(
    view: FlowGraph | None, member: RouteMember, entry_id: str, known: set[str]
) -> list[str]:
    out: list[str] = []
    if member.happy is None or not member.happy.node_ids:
        return ["member.happy missing or empty"]
    if member.happy.node_ids[0] != entry_id:
        out.append("member happy first is not entry")
    out.extend(f"member happy node {i} not in graph" for i in member.happy.node_ids if i not in known)
    if view is None:
        return out + ["slice is None"]
    nodes = {n.id: n for n in view.nodes}
    out.extend(_payload_failures(view, entry_id, nodes))
    if view.meta.get("visible_before_promote", 0) > DEFAULT_BUDGET:
        out.append(f"visible_before_promote {view.meta['visible_before_promote']} > {DEFAULT_BUDGET}")
    return out


def _twin_failures(entry: FlowNode, paths: dict[str, list[str]]) -> dict[str, list[str]]:
    groups: dict[tuple, list[RouteMember]] = {}
    for m in entry.members:
        groups.setdefault((m.handler_fqn, tuple(m.wrappers)), []).append(m)
    out: dict[str, list[str]] = {}
    for twins in groups.values():
        keys = {tuple(paths.get(f"{m.method} {m.path}", [])) for m in twins}
        if len(keys) > 1:
            for m in twins:
                out[f"{m.method} {m.path}"] = ["twin members differ in payload"]
    return out


def _entries(graph: FlowGraph) -> list[FlowNode]:
    return sorted(
        (n for n in graph.nodes
         if n.kind == "entry" and n.id.startswith("entry:") and not n.id.startswith("entry:seed:")),
        key=lambda n: n.id,
    )


def _row(entry: FlowNode, member: RouteMember, view: FlowGraph | None, reasons: list[str]) -> str:
    payload = (view.meta.get("happy") if view else None) or {}
    ids = payload.get("node_ids") or []
    nodes = {n.id: n for n in view.nodes} if view else {}
    last = nodes[ids[-1]].label if ids and ids[-1] in nodes else "-"
    before = view.meta.get("visible_before_promote", "-") if view else "-"
    after = _visible(view) if view else "-"
    verdict = "OK" if not reasons else "FAIL(" + "; ".join(reasons) + ")"
    handler = member.handler_fqn.rsplit(".", 1)[-1]
    return (
        f"{entry.id} | {handler} | {member.method} {member.path} | {len(ids)} | {before} | "
        f"{after} | {bool(payload.get('ends_in_failure'))} | {last} | {verdict}"
    )


def main() -> int:
    out_dir = Path(sys.argv[1])
    graph = FlowGraph.model_validate(json.loads((out_dir / "flow_graph.json").read_text(encoding="utf-8")))
    known = {n.id for n in graph.nodes}
    routes = build_route_subgraph()
    overview = EndpointSubgraph()
    total = failures = failing_ends = 0
    visible_counts: list[int] = []
    print("entry | handler | route | path len | before | after | ends_in_failure | last | verdict")
    for entry in _entries(graph):
        views = [
            (m, routes.slice(graph, entry.id, m.handler_fqn) if m.handler_fqn else None)
            for m in entry.members
        ]
        paths = {
            f"{m.method} {m.path}": ((v.meta.get("happy") or {}).get("node_ids") or [])
            for m, v in views if v is not None
        }
        twins = _twin_failures(entry, paths)
        for member, view in views:
            reasons = _route_failures(view, member, entry.id, known)
            reasons += twins.get(f"{member.method} {member.path}", [])
            print(_row(entry, member, view, reasons))
            total += 1
            failures += bool(reasons)
            if view is not None:
                visible_counts.append(_visible(view))
                failing_ends += bool((view.meta.get("happy") or {}).get("ends_in_failure"))
    print("\nentry overviews (information only)")
    for entry in _entries(graph):
        view = overview.slice(graph, entry.id)
        count = _visible(view) if view else 0
        print(f"{entry.id}: {count} visible{'  OVER 16' if count > 16 else ''}")
    mean = sum(visible_counts) / len(visible_counts) if visible_counts else 0.0
    print(
        f"\nroutes={total} failures={failures} ends_in_failure={failing_ends} "
        f"visible max={max(visible_counts, default=0)} mean={mean:.1f}"
    )
    return 1 if failures or total == 0 else 0


if __name__ == "__main__":
    sys.exit(main())

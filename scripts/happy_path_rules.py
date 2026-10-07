import itertools

from shared.flow_endpoints.endpoint_elider import DEFAULT_BUDGET
from shared.models.flow_graph import FlowGraph, FlowNode, RouteMember

MAX_LEAF_ROUTES = 8


def visible_count(view: FlowGraph) -> int:
    return sum(1 for n in view.nodes if n.level == 0)


def is_dag(view: FlowGraph) -> bool:
    indegree = {n.id: 0 for n in view.nodes}
    out: dict[str, list[str]] = {}
    for e in view.edges:
        if e.source in indegree and e.target in indegree:
            indegree[e.target] += 1
            out.setdefault(e.source, []).append(e.target)
    ready = [i for i, d in indegree.items() if d == 0]
    seen = 0
    while ready:
        node = ready.pop()
        seen += 1
        for nxt in out.get(node, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
    return seen == len(indegree)


def find_path(view: FlowGraph, member: RouteMember) -> list[dict]:
    return [
        p for p in view.meta.get("paths") or []
        if (p["method"], p["path"], p["handler_fqn"])
        == (member.method, member.path, member.handler_fqn)
    ]


def _reveal_failures(
    nodes: dict[str, FlowNode], ids: list[str], reveal: set[str]
) -> list[str]:
    parents: dict[str, str] = {}
    for node in nodes.values():
        for child in node.hidden_children:
            parents.setdefault(child, node.id)
    out: list[str] = []
    for node_id in ids:
        current = node_id
        seen: set[str] = set()
        while nodes[current].level > 0:
            host = parents.get(current)
            if host is None or host in seen or host not in nodes:
                out.append(f"{node_id} has no host chain to level 0")
                break
            if host not in reveal:
                out.append(f"{node_id} host {host} not in reveal")
            seen.add(host)
            current = host
    visible = {i for i, n in nodes.items() if n.level == 0}
    frontier = [i for i in visible if i in reveal]
    while frontier:
        for child in nodes[frontier.pop()].hidden_children:
            if child in nodes and child not in visible:
                visible.add(child)
                if child in reveal:
                    frontier.append(child)
    out.extend(f"{i} not visible after simulated reveal" for i in ids if i not in visible)
    return out


def _edge_failures(view: FlowGraph, entry: dict) -> list[str]:
    ids = entry["node_ids"]
    direct = {(e.source, e.target) for e in view.edges}
    listed = {tuple(e) for e in entry.get("edges") or []}
    out = [f"missing_edges {entry['missing_edges']}"] if entry.get("missing_edges") else []
    for pair in itertools.pairwise(ids):
        if pair not in direct:
            out.append(f"no edge {pair[0]} -> {pair[1]}")
        if pair not in listed:
            out.append(f"edge {pair[0]} -> {pair[1]} not in payload edges")
    return out


def route_failures(
    view: FlowGraph | None, member: RouteMember, entry_id: str, known: set[str]
) -> list[str]:
    ids = member.happy.node_ids if member.happy else []
    if not ids:
        return ["member.happy missing or empty"]
    out: list[str] = []
    if ids[0] != entry_id:
        out.append("member happy first is not entry")
    out.extend(f"member happy node {i} not in graph" for i in ids if i not in known)
    if view is None:
        return out + ["leaf view is None"]
    matches = find_path(view, member)
    if len(matches) != 1:
        return out + [f"{len(matches)} path entries in leaf"]
    entry = matches[0]
    pids: list[str] = entry["node_ids"]
    nodes = {n.id: n for n in view.nodes}
    if not pids:
        return out + ["payload empty"]
    if pids[0] != entry_id:
        out.append("payload first is not view root")
    if len(set(pids)) != len(pids):
        out.append("payload has duplicates")
    absent = [i for i in pids if i not in nodes]
    out.extend(f"payload node {i} missing from view" for i in absent)
    if not absent:
        out.extend(_reveal_failures(nodes, pids, set(entry["reveal"])))
        last = nodes[pids[-1]]
        terminal = last.kind == "outcome" or last.effect_kind == "response"
        if not terminal and not entry["ends_in_failure"]:
            out.append(f"path ends on {last.kind} {pids[-1]}")
    out.extend(_edge_failures(view, entry))
    before = view.meta.get("visible_before_promote", 0)
    if before > DEFAULT_BUDGET:
        out.append(f"visible_before_promote {before} > {DEFAULT_BUDGET}")
    return out


def twin_failures(members: list[RouteMember], view: FlowGraph | None) -> dict[tuple, str]:
    if view is None:
        return {}
    groups: dict[tuple, list[RouteMember]] = {}
    for m in members:
        groups.setdefault((m.handler_fqn, tuple(m.wrappers)), []).append(m)
    out: dict[tuple, str] = {}
    for twins in groups.values():
        keys = {tuple(p["node_ids"]) for m in twins for p in find_path(view, m)}
        if len(keys) > 1:
            out.update({(m.method, m.path, m.handler_fqn): "twin payloads differ" for m in twins})
    return out

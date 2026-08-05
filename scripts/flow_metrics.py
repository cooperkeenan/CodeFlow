import collections
import json
import sys
from pathlib import Path


def _load(out_dir: Path) -> tuple[dict, dict]:
    graph = json.loads((out_dir / "flow_graph.json").read_text())
    view = json.loads((out_dir / "rendered_view.json").read_text())
    return graph, view


def _bodies(nodes: dict[str, dict]) -> dict[str, list[str]]:
    return {i: n["hidden_children"] for i, n in nodes.items() if n["hidden_children"]}


def _subtree(owner: str, bodies: dict[str, list[str]]) -> set[str]:
    seen: set[str] = set()
    queue = list(bodies.get(owner, []))
    while queue:
        member = queue.pop()
        if member in seen:
            continue
        seen.add(member)
        queue.extend(bodies.get(member, []))
    return seen


def _single_entry_gaps(
    owner: str, members: list[str], bodies: dict[str, list[str]], inbound: dict[str, set[str]]
) -> list[str]:
    scope = _subtree(owner, bodies) | {owner}
    return sorted(m for m in members if not (inbound[m] & scope))


def _containment_depth(nodes: dict[str, dict], repo: str) -> dict[str, int]:
    depth: dict[str, int] = {}

    def resolve(node_id: str, seen: frozenset[str]) -> int:
        if node_id in depth:
            return depth[node_id]
        containers = [c for c in nodes[node_id]["containers"] if c in nodes and c not in seen]
        value = 0 if not containers else 1 + min(
            resolve(c, seen | {node_id}) for c in containers
        )
        depth[node_id] = value
        return value

    for node_id in sorted(nodes):
        resolve(node_id, frozenset())
    return depth


def _overlaps(view: dict) -> list[tuple[str, str]]:
    geometry = view["node_geometry"]
    boxes: list[tuple[str, float, float, float, float]] = []
    for node in view["nodes"]:
        size = geometry.get(node.get("shape") or node["kind"])
        if not size:
            continue
        pos = node["position"]
        boxes.append((node["id"], pos["x"], pos["y"], size["width"], size["height"]))
    hits: list[tuple[str, str]] = []
    for i in range(len(boxes)):
        aid, ax, ay, aw, ah = boxes[i]
        for j in range(i + 1, len(boxes)):
            bid, bx, by, bw, bh = boxes[j]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                hits.append((aid, bid))
    return sorted(hits)


def report(out_dir: Path) -> int:
    graph, view = _load(out_dir)
    nodes = {n["id"]: n for n in graph["nodes"]}
    bodies = _bodies(nodes)
    inbound: dict[str, set[str]] = collections.defaultdict(set)
    for edge in graph["edges"]:
        inbound[edge["target"]].add(edge["source"])

    print(f"repo              {graph['repo']}")
    print(f"nodes / edges     {len(nodes)} / {len(graph['edges'])}")
    print(f"  edge kinds      {dict(collections.Counter(e['kind'] for e in graph['edges']))}")
    print(f"  synthesized     {sum(1 for e in graph['edges'] if e['hidden_path'])}")
    print(f"kinds             {dict(collections.Counter(n['kind'] for n in nodes.values()))}")

    roots = sorted(i for i, n in nodes.items() if not n["containers"])
    depth = _containment_depth(nodes, graph["repo"])
    print(f"roots             {len(roots)} {roots if len(roots) <= 3 else ''}")
    print(f"depth             {dict(sorted(collections.Counter(depth.values()).items()))}")

    skeleton = [i for i, n in nodes.items() if n["level"] == 0]
    print(f"skeleton (lvl 0)  {len(skeleton)}  (budget 15)")

    sizes = collections.Counter(len(m) for m in bodies.values())
    kinds = collections.Counter(nodes[o]["body_kind"] for o in bodies)
    multi = {o: m for o, m in bodies.items() if len(m) > 1}
    print(f"bodies            {len(bodies)}  (multi-member {len(multi)})")
    print(f"  size dist       {dict(sorted(sizes.items()))}")
    print(f"  body_kind       {dict(sorted(kinds.items()))}")
    forks = sorted(o for o, m in multi.items() if nodes[o]["kind"] == "decision")
    labelled = [
        o for o in forks
        if all(nodes[c]["kind"] == "outcome" for c in bodies[o])
    ]
    seqs = {o: m for o, m in multi.items() if nodes[o]["kind"] != "decision"}
    chains = [o for o, m in seqs.items() if nodes[o]["body_kind"] == "flow"]
    print(f"  decision forks  {len(forks)}  ({len(labelled)} fork only to outcomes)")
    print(f"  sequence bodies {len(seqs)}  ({len(chains)} are chains)")

    flow_multi = {o: m for o, m in multi.items() if nodes[o]["body_kind"] != "list"}
    gaps = {o: g for o, m in flow_multi.items() if (g := _single_entry_gaps(o, m, bodies, inbound))}
    cohesion: dict[str, tuple[int, int]] = {}
    for owner, members in flow_multi.items():
        member_set = set(members)
        internal = sum(
            1 for e in graph["edges"] if e["source"] in member_set and e["target"] in member_set
        )
        if internal < len(members) - 1:
            cohesion[owner] = (internal, len(members) - 1)

    print(f"I3 single-entry   {len(flow_multi) - len(gaps)}/{len(flow_multi)} flow bodies clean")
    for owner, gap in sorted(gaps.items())[:5]:
        print(f"    GAP {owner[:58]} -> {gap[:2]}")
    print(f"I5 cohesion       {len(cohesion)} violations")
    for owner, (got, want) in sorted(cohesion.items())[:5]:
        print(f"    VIOL {owner[:58]} {got} < {want}")

    unreachable = sorted(set(nodes) - {r for r in roots} - {
        m for owner in roots for m in _subtree(owner, bodies)
    })
    print(f"I2 unreachable    {len(unreachable)} {unreachable[:3] if unreachable else ''}")

    hits = _overlaps(view)
    print(f"OVERLAPS          {len(hits)} {hits[:2] if hits else ''}")
    return 1 if (cohesion or unreachable or hits or len(roots) != 1) else 0


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "scratch_out").resolve()
    raise SystemExit(report(target))

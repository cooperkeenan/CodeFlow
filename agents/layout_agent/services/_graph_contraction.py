from collections import deque
from dataclasses import dataclass

_PRIMARY = frozenset({"service", "orchestrator", "repository", "entry"})
_ADAPTER = frozenset({"tool", "client", "helper"})


@dataclass
class ContractionResult:
    names: set[str]
    edges: list[tuple[str, str]]
    folded: dict[str, list[str]]


def contract(
    names: set[str],
    edges: list[tuple[str, str]],
    roles: dict[str, str],
) -> ContractionResult:
    callees_map: dict[str, list[str]] = {n: [] for n in names}
    for s, t in edges:
        if s in names and t in names and s != t:
            callees_map[s].append(t)

    fold_map: dict[str, str] = {}
    folded: dict[str, list[str]] = {}
    for name in names:
        if roles.get(name, "") in _ADAPTER and len(callees_map.get(name, [])) == 1:
            survivor = callees_map[name][0]
            fold_map[name] = survivor
            folded.setdefault(survivor, []).append(name)

    contracted_names = names - set(fold_map)
    seen: set[tuple[str, str]] = set()
    contracted_edges: list[tuple[str, str]] = []
    for s, t in edges:
        ns, nt = fold_map.get(s, s), fold_map.get(t, t)
        if ns != nt and ns in contracted_names and nt in contracted_names:
            key = (ns, nt)
            if key not in seen:
                seen.add(key)
                contracted_edges.append(key)

    return ContractionResult(names=contracted_names, edges=contracted_edges, folded=folded)


def bfs_depth(root: str, names: set[str], edges: list[tuple[str, str]]) -> dict[str, int]:
    adj: dict[str, list[str]] = {n: [] for n in names}
    for s, t in edges:
        adj[s].append(t)
    depth: dict[str, int] = {}
    q: deque = deque([(root, 0)] if root else [])
    seen: set[str] = {root} if root else set()
    while q:
        node, d = q.popleft()
        depth[node] = d
        for nxt in adj.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, d + 1))
    for n in names:
        depth.setdefault(n, 0)
    return depth

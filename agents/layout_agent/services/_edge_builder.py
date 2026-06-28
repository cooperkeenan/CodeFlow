from collections import deque

from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import TemplateEdge

_SEQ = "sequence"


def build(
    diagram_type: str,
    focus: str,
    callers: list[str],
    callees: list[str],
    children: list[str],
    override_order: list[str] | None,
    spec: DiagramSpec,
) -> tuple[list[TemplateEdge], list[str] | None]:
    steps = {*callees, *children}
    if diagram_type == "pipeline":
        return _pipeline(focus, callers, steps, override_order, spec)
    if diagram_type == "hierarchy":
        return _tree(focus, callers, steps, spec), None
    if diagram_type == "layered_tier":
        depth = {focus: 0, **{c: -1 for c in callers}, **{n: 1 for n in steps}}
        return _layered(steps | {focus, *callers}, depth, spec), None
    return _raw({focus, *callers, *steps}, focus, set(callers), list(children), spec), None


def build_structural(
    diagram_type: str,
    names: set[str],
    intra: list[tuple[str, str]],
) -> tuple[list[TemplateEdge], list[str] | None]:
    if diagram_type == "pipeline":
        ordered = _topo(list(names), intra)
        edges: list[TemplateEdge] = []
        for i in range(len(ordered) - 1):
            edges.append(TemplateEdge(source=ordered[i], target=ordered[i + 1], edge_type=_SEQ))
        return edges, ordered
    return [TemplateEdge(source=s, target=t, edge_type="call") for s, t in intra], None


def _pipeline(
    focus: str, callers: list[str], steps: set[str],
    override_order: list[str] | None, spec: DiagramSpec,
) -> tuple[list[TemplateEdge], list[str]]:
    ordered = [n for n in (override_order or []) if n in steps]
    if not ordered:
        step_pairs = [(e.source, e.target) for e in spec.edges if e.source in steps and e.target in steps]
        ordered = _topo(list(steps), step_pairs)
    caller_types = {e.source: e.edge_type for e in spec.edges if e.target == focus and e.source in callers}
    edges: list[TemplateEdge] = [
        TemplateEdge(source=c, target=focus, edge_type=caller_types.get(c, "call")) for c in callers
    ]
    chain = [focus] + ordered
    for i in range(len(chain) - 1):
        edges.append(TemplateEdge(source=chain[i], target=chain[i + 1], edge_type=_SEQ))
    return edges, ordered


def _tree(focus: str, callers: list[str], steps: set[str], spec: DiagramSpec) -> list[TemplateEdge]:
    caller_types = {e.source: e.edge_type for e in spec.edges if e.target == focus and e.source in callers}
    edges: list[TemplateEdge] = [
        TemplateEdge(source=c, target=focus, edge_type=caller_types.get(c, "call")) for c in callers
    ]
    for n in steps:
        edges.append(TemplateEdge(source=focus, target=n, edge_type="call"))
    return edges


def _layered(involved: set[str], depth: dict[str, int], spec: DiagramSpec) -> list[TemplateEdge]:
    seen: set[tuple[str, str]] = set()
    edges: list[TemplateEdge] = []
    for e in spec.edges:
        if (e.source in involved and e.target in involved and e.source != e.target
                and e.edge_type != "import" and depth.get(e.target, 0) >= depth.get(e.source, 0)):
            key = (e.source, e.target)
            if key not in seen:
                seen.add(key)
                edges.append(TemplateEdge(source=e.source, target=e.target, edge_type=e.edge_type))
    return edges


def _raw(involved: set[str], focus: str, callers: set[str], children: list[str], spec: DiagramSpec) -> list[TemplateEdge]:
    seen: set[tuple[str, str]] = set()
    edges: list[TemplateEdge] = []
    for e in spec.edges:
        if (e.edge_type != "import" and e.source != e.target
                and e.source in involved and e.target in involved
                and not (e.source in callers and e.target != focus)):
            key = (e.source, e.target)
            if key not in seen:
                seen.add(key)
                edges.append(TemplateEdge(source=e.source, target=e.target, edge_type=e.edge_type))
    for child in children:
        key = (focus, child)
        if key not in seen:
            seen.add(key)
            edges.append(TemplateEdge(source=focus, target=child, edge_type="call"))
    return edges


def _topo(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    in_deg = {n: 0 for n in nodes}
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for s, t in edges:
        if s in in_deg and t in in_deg:
            adj[s].append(t)
            in_deg[t] += 1
    q: deque = deque(n for n in nodes if in_deg[n] == 0)
    result: list[str] = []
    while q:
        n = q.popleft()
        result.append(n)
        for nxt in adj[n]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                q.append(nxt)
    result.extend(n for n in nodes if n not in result)
    return result

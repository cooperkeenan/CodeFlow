from shared.models.flow_graph import EdgeKind, FlowEdge, FlowGraph, FlowNode, Lane

_EdgeKey = tuple[str, str, str, str]


class BudgetWorkGraph:
    def __init__(self, graph: FlowGraph) -> None:
        self.repo = graph.repo
        self.page_title = graph.page_title
        self.meta = dict(graph.meta)
        self.lanes: list[Lane] = [lane.model_copy(deep=True) for lane in graph.lanes]
        self.nodes: dict[str, FlowNode] = {n.id: n.model_copy(deep=True) for n in graph.nodes}
        self.edges: dict[_EdgeKey, FlowEdge] = {}
        for edge in graph.edges:
            self.edges[self._key(edge)] = edge.model_copy(deep=True)

    def _key(self, edge: FlowEdge) -> _EdgeKey:
        return (edge.source, edge.target, edge.kind, edge.arm_label)

    def out_edges(self, node_id: str) -> list[FlowEdge]:
        return [e for e in self.edges.values() if e.source == node_id]

    def in_edges(self, node_id: str) -> list[FlowEdge]:
        return [e for e in self.edges.values() if e.target == node_id]

    def arm_edges(self, node_id: str) -> list[FlowEdge]:
        return [e for e in self.edges.values() if e.source == node_id and e.kind == "arm"]

    def add_edge(self, source: str, target: str, kind: EdgeKind, arm_label: str = "") -> None:
        if source == target:
            return
        key = (source, target, kind, arm_label)
        if key not in self.edges:
            self.edges[key] = FlowEdge(source=source, target=target, kind=kind, arm_label=arm_label)

    def remove_edge(self, edge: FlowEdge) -> None:
        self.edges.pop(self._key(edge), None)

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        for key in [k for k in self.edges if k[0] == node_id or k[1] == node_id]:
            del self.edges[key]

    def lane_node_count(self, lane_id: str) -> int:
        return sum(1 for n in self.nodes.values() if n.lane == lane_id)

    def entry_ids(self) -> list[str]:
        return sorted(n.id for n in self.nodes.values() if n.kind == "entry")

    def _adjacency(self, exclude: frozenset[str]) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = {}
        for edge in self.edges.values():
            if edge.source in exclude or edge.target in exclude:
                continue
            adj.setdefault(edge.source, []).append(edge.target)
        return adj

    def reachable(self, exclude: frozenset[str] = frozenset()) -> set[str]:
        adj = self._adjacency(exclude)
        seen: set[str] = set()
        stack = [nid for nid in self.entry_ids() if nid not in exclude]
        while stack:
            node_id = stack.pop()
            if node_id in seen:
                continue
            seen.add(node_id)
            stack.extend(adj.get(node_id, ()))
        return seen

    def reachable_from(self, start: str) -> set[str]:
        adj = self._adjacency(frozenset())
        seen: set[str] = set()
        stack = [start]
        while stack:
            node_id = stack.pop()
            if node_id in seen:
                continue
            seen.add(node_id)
            stack.extend(adj.get(node_id, ()))
        return seen

    def prune_unreachable(self) -> None:
        keep = self.reachable()
        for node_id in [nid for nid in self.nodes if nid not in keep]:
            self.remove_node(node_id)

    def to_flow_graph(self) -> FlowGraph:
        return FlowGraph(
            repo=self.repo,
            page_title=self.page_title,
            lanes=self.lanes,
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
            meta=self.meta,
        )

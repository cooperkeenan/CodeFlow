from shared.models.flow_graph import FlowEdge, FlowGraph, FlowNode

_WALKABLE = frozenset({"sequence", "arm", "parallel"})


class PathGraph:
    def __init__(self, graph: FlowGraph) -> None:
        self._nodes = {n.id: n for n in graph.nodes}
        self._out: dict[str, list[FlowEdge]] = {}
        for edge in graph.edges:
            if edge.kind in _WALKABLE and edge.target in self._nodes:
                self._out.setdefault(edge.source, []).append(edge)
        for edges in self._out.values():
            edges.sort(key=lambda e: (e.arm_index < 0, e.arm_index, e.target, e.kind))
        self._entries = frozenset(n.id for n in graph.nodes if n.kind == "entry")
        handlers = frozenset(
            m.handler_fqn for n in graph.nodes if n.kind == "entry" for m in n.members
        )
        self._heads = frozenset(
            m.head
            for n in graph.nodes
            if n.kind == "entry"
            for m in n.members
            if m.head in self._nodes and self._nodes[m.head].owner_fqn in handlers
        )

    def node(self, node_id: str) -> FlowNode | None:
        return self._nodes.get(node_id)

    def out(self, node_id: str) -> list[FlowEdge]:
        return self._out.get(node_id, [])

    def is_entry(self, node_id: str) -> bool:
        return node_id in self._entries

    def owner(self, node_id: str) -> str:
        return self._nodes[node_id].owner_fqn

    def line(self, node_id: str) -> int:
        refs = self._nodes[node_id].refs
        return refs[0].line if refs else 0

    def is_walkable_target(self, target: str, own_head: str) -> bool:
        if target in self._entries:
            return False
        return target == own_head or target not in self._heads

from shared.models.flow_graph import FlowEdge, FlowNode


class SliceGraph:
    def __init__(
        self,
        nodes: dict[str, FlowNode],
        edges: list[FlowEdge],
        root_id: str,
        external: dict[str, list[str]] | None = None,
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.root_id = root_id
        self.external = external or {}
        self.keep: set[str] = set(nodes)
        self.pinned: set[str] = set()
        self.protected: set[str] = set()
        self.pins: list[str] = []
        self.aliases: dict[str, str] = {}
        self.visible_before_promote = 0

    def resolve(self, node_id: str) -> str:
        seen = {node_id}
        while node_id in self.aliases and self.aliases[node_id] not in seen:
            node_id = self.aliases[node_id]
            seen.add(node_id)
        return node_id

    def set_pins(self, pins: list[str]) -> None:
        self.pins = list(pins)
        resolved = {self.resolve(pin) for pin in pins}
        self.pinned = {node_id for node_id in resolved if node_id in self.nodes}

    def set_protected(self, ids: list[str]) -> None:
        resolved = {self.resolve(node_id) for node_id in ids}
        self.protected = {node_id for node_id in resolved if node_id in self.nodes}

    def resolve_path(self, ids: list[str]) -> list[str]:
        out: list[str] = []
        for node_id in (self.resolve(i) for i in ids):
            if node_id not in self.nodes:
                continue
            if node_id in out:
                del out[out.index(node_id) + 1 :]
            else:
                out.append(node_id)
        return out

    def path(self) -> list[str]:
        resolved = [self.resolve(pin) for pin in self.pins]
        resolved = [node_id for node_id in resolved if node_id in self.nodes]
        return [n for i, n in enumerate(resolved) if i == 0 or n != resolved[i - 1]]

    def successors(self, node_id: str) -> list[str]:
        return sorted({e.target for e in self.edges if e.source == node_id})

    def predecessors(self, node_id: str) -> list[str]:
        return sorted({e.source for e in self.edges if e.target == node_id})

    def out_degree(self, node_id: str) -> int:
        return len(self.successors(node_id))

    def in_degree(self, node_id: str) -> int:
        return len(self.predecessors(node_id))

    def arm_count(self, node_id: str) -> int:
        return sum(1 for e in self.edges if e.source == node_id and e.kind == "arm")

    def is_fork(self, node_id: str) -> bool:
        return self.nodes[node_id].kind == "decision" and self.arm_count(node_id) >= 2

    def add_node(self, node: FlowNode) -> None:
        self.nodes[node.id] = node
        self.keep.add(node.id)

    def add_edge(
        self, source: str, target: str, kind: str = "sequence", arm_label: str = "", arm_index: int = -1
    ) -> None:
        if source == target:
            return
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return
        self.edges.append(FlowEdge(
                source=source, target=target, kind=kind, arm_label=arm_label, arm_index=arm_index
            )
        )

    def absorb(self, members: set[str], host_id: str) -> None:
        inner = members - {host_id}
        if not inner:
            return
        self._repoint(inner, host_id)
        for member_id in inner:
            self.aliases[member_id] = host_id
        if inner & self.pinned:
            self.pinned = (self.pinned - inner) | {host_id}
        if inner & self.protected:
            self.protected = (self.protected - inner) | {host_id}
        for member_id in sorted(inner):
            self.nodes[member_id].containers = [host_id]
            self.keep.discard(member_id)

    def drop(self, node_id: str) -> None:
        incoming = [(e.source, e.kind, e.arm_label, e.arm_index) for e in self.edges if e.target == node_id]
        outgoing = sorted({e.target for e in self.edges if e.source == node_id})
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]
        for source, kind, arm_label, arm_index in sorted(incoming):
            for target in outgoing:
                self.add_edge(source, target, kind, arm_label, arm_index)
        parent = self.nodes[node_id].containers[0] if self.nodes[node_id].containers else ""
        self.nodes.pop(node_id, None)
        self.keep.discard(node_id)
        for node in self.nodes.values():
            if node_id in node.containers:
                rest = [c for c in node.containers if c != node_id]
                node.containers = rest or ([parent] if parent in self.nodes else [])

    def _repoint(self, inner: set[str], host_id: str) -> None:
        rewritten: list[FlowEdge] = []
        seen: set[tuple[str, str, str, str]] = set()
        for edge in self.edges:
            source = host_id if edge.source in inner else edge.source
            target = host_id if edge.target in inner else edge.target
            if source == target:
                continue
            key = (source, target, edge.kind, edge.arm_label)
            if key in seen:
                continue
            seen.add(key)
            copy = edge.model_copy(deep=True)
            copy.source = source
            copy.target = target
            rewritten.append(copy)
        self.edges = rewritten

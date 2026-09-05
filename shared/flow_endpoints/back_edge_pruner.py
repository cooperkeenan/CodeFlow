from shared.models.flow_graph import FlowEdge


class BackEdgePruner:
    def prune(self, node_ids: set[str], edges: list[FlowEdge], root_id: str) -> list[FlowEdge]:
        ordered = sorted(
            edges, key=lambda e: (e.source, e.target, e.kind, e.arm_label, e.group_id)
        )
        outgoing: dict[str, list[tuple[int, FlowEdge]]] = {node_id: [] for node_id in node_ids}
        for index, edge in enumerate(ordered):
            outgoing[edge.source].append((index, edge))
        dropped: set[int] = set()
        done: set[str] = set()
        for start in [root_id] + sorted(node_ids - {root_id}):
            if start not in done:
                self._walk(start, outgoing, done, dropped)
        return [edge for index, edge in enumerate(ordered) if index not in dropped]

    def _walk(
        self,
        start: str,
        outgoing: dict[str, list[tuple[int, FlowEdge]]],
        done: set[str],
        dropped: set[int],
    ) -> None:
        on_stack = {start}
        stack: list[tuple[str, int]] = [(start, 0)]
        while stack:
            node_id, cursor = stack.pop()
            children = outgoing[node_id]
            if cursor >= len(children):
                on_stack.discard(node_id)
                done.add(node_id)
                continue
            stack.append((node_id, cursor + 1))
            index, edge = children[cursor]
            if edge.target in on_stack:
                dropped.add(index)
            elif edge.target not in done:
                on_stack.add(edge.target)
                stack.append((edge.target, 0))

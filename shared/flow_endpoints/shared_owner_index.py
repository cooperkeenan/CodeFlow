from shared.models.flow_graph import FlowGraph, FlowNode

_ENTRY_PREFIX = "entry:"


class SharedOwnerIndex:
    def counts(self, graph: FlowGraph) -> dict[str, int]:
        nodes_by_id = {node.id: node for node in graph.nodes}
        totals: dict[str, int] = {}
        for node in graph.nodes:
            if node.kind != "entry" or not node.id.startswith(_ENTRY_PREFIX):
                continue
            owners = {
                nodes_by_id[member].owner_fqn
                for member in self._closure(node.id, nodes_by_id)
                if nodes_by_id[member].owner_fqn
            }
            for owner in owners:
                totals[owner] = totals.get(owner, 0) + 1
        return totals

    def _closure(self, entry_id: str, nodes_by_id: dict[str, FlowNode]) -> set[str]:
        seen = {entry_id}
        stack = [entry_id]
        while stack:
            current = stack.pop()
            for child_id in nodes_by_id[current].hidden_children:
                if child_id in nodes_by_id and child_id not in seen:
                    seen.add(child_id)
                    stack.append(child_id)
        return seen

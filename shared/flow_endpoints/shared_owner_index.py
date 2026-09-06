from shared.models.flow_graph import FlowGraph, FlowNode

_ENTRY_PREFIX = "entry:"


class SharedOwnerIndex:
    def owners(self, graph: FlowGraph) -> dict[str, list[str]]:
        nodes_by_id = {node.id: node for node in graph.nodes}
        totals: dict[str, list[str]] = {}
        for node in graph.nodes:
            if node.kind != "entry" or not node.id.startswith(_ENTRY_PREFIX):
                continue
            owners = {
                nodes_by_id[member].owner_fqn
                for member in self._closure(node.id, nodes_by_id)
                if nodes_by_id[member].owner_fqn
            }
            for owner in owners:
                totals.setdefault(owner, []).append(node.id)
        return {owner: sorted(entries) for owner, entries in totals.items()}

    def counts(self, graph: FlowGraph) -> dict[str, int]:
        return {owner: len(entries) for owner, entries in self.owners(graph).items()}

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

from services.analysis.budget_work_graph import BudgetWorkGraph


class SpineProtector:
    def compute(self, graph: BudgetWorkGraph) -> frozenset[str]:
        parent = self._bfs_parents(graph)
        decisions = sorted(n.id for n in graph.nodes.values() if n.kind == "decision")
        protected: set[str] = set()
        for decision_id in decisions:
            node_id: str | None = decision_id
            while node_id is not None and node_id not in protected:
                protected.add(node_id)
                node_id = parent.get(node_id)
        return frozenset(protected)

    def _bfs_parents(self, graph: BudgetWorkGraph) -> dict[str, str]:
        parent: dict[str, str] = {}
        seen: set[str] = set(graph.entry_ids())
        queue: list[str] = sorted(seen)
        index = 0
        while index < len(queue):
            current = queue[index]
            index += 1
            targets = sorted(
                edge.target for edge in graph.out_edges(current) if edge.kind != "stitch"
            )
            for target in targets:
                if target in seen:
                    continue
                seen.add(target)
                parent[target] = current
                queue.append(target)
        return parent

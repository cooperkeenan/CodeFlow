from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph

from shared.models.flow_graph import FlowEdge

_MAX_HIDDEN_DEPTH = 8


class SkeletonProjector:
    def project(self, graph: BudgetWorkGraph) -> list[FlowEdge]:
        skeleton_ids = frozenset(
            node.id for node in graph.nodes.values() if node.level == 0
        )
        best: dict[tuple[str, str], list[str]] = {}
        for start in sorted(graph.nodes):
            if start not in skeleton_ids:
                continue
            for target, hidden_path in self._walk(graph, start, skeleton_ids):
                key = (start, target)
                current = best.get(key)
                if current is None or self._rank(hidden_path) < self._rank(current):
                    best[key] = hidden_path
        return [
            FlowEdge(source=source, target=target, kind="sequence", hidden_path=hidden_path)
            for (source, target), hidden_path in sorted(best.items())
            if hidden_path
        ]

    def _rank(self, path: list[str]) -> tuple[int, tuple[str, ...]]:
        return (len(path), tuple(path))

    def _walk(
        self, graph: BudgetWorkGraph, start: str, skeleton_ids: frozenset[str]
    ) -> list[tuple[str, list[str]]]:
        results: list[tuple[str, list[str]]] = []
        self._dfs(graph, start, start, [], set(), skeleton_ids, results)
        return results

    def _dfs(
        self,
        graph: BudgetWorkGraph,
        start: str,
        current: str,
        hidden_path: list[str],
        visited: set[str],
        skeleton_ids: frozenset[str],
        results: list[tuple[str, list[str]]],
    ) -> None:
        edges = sorted(
            graph.out_edges(current), key=lambda edge: (edge.target, edge.kind, edge.arm_label)
        )
        for edge in edges:
            nxt = edge.target
            if nxt == start or nxt in visited:
                continue
            if nxt in skeleton_ids:
                results.append((nxt, list(hidden_path)))
                continue
            if len(hidden_path) >= _MAX_HIDDEN_DEPTH:
                continue
            visited.add(nxt)
            hidden_path.append(nxt)
            self._dfs(graph, start, nxt, hidden_path, visited, skeleton_ids, results)
            hidden_path.pop()
            visited.discard(nxt)

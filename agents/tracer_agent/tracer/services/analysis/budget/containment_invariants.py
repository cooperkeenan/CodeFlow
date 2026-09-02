from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph


class ContainmentInvariants:
    def enforce_structure(self, graph: BudgetWorkGraph) -> None:
        self._assert_dag(graph)
        self._assert_total(graph)

    def enforce_bodies(self, graph: BudgetWorkGraph) -> None:
        self._assert_cohesion(graph)

    def termination_violators(self, graph: BudgetWorkGraph) -> list[str]:
        return sorted(
            node_id
            for node_id, node in graph.nodes.items()
            if node.kind == "decision" and not graph.out_edges(node_id)
        )

    def flow_list_split(self, graph: BudgetWorkGraph) -> tuple[int, int]:
        flow = sum(
            1 for n in graph.nodes.values() if n.hidden_children and n.body_kind == "flow"
        )
        lst = sum(
            1 for n in graph.nodes.values() if n.hidden_children and n.body_kind == "list"
        )
        return flow, lst

    def border_count(self, graph: BudgetWorkGraph) -> int:
        count = 0
        for owner, node in graph.nodes.items():
            members = node.hidden_children
            if not members:
                continue
            member_set = set(members)
            tails = set(node.body_tails)
            for member in members:
                if member in tails:
                    continue
                for edge in graph.out_edges(member):
                    if edge.target not in member_set:
                        count += 1
        return count

    def _assert_dag(self, graph: BudgetWorkGraph) -> None:
        for node_id in sorted(graph.nodes):
            for container in graph.nodes[node_id].containers:
                assert container in graph.nodes, (
                    f"{node_id} has missing container {container}"
                )

        def ancestors(node_id: str, seen: frozenset[str]) -> None:
            for container in graph.nodes[node_id].containers:
                assert container not in seen, f"containment cycle at {node_id} -> {container}"
                ancestors(container, seen | {container})

        for node_id in sorted(graph.nodes):
            ancestors(node_id, frozenset({node_id}))

    def _assert_total(self, graph: BudgetWorkGraph) -> None:
        roots = sorted(nid for nid in graph.nodes if not graph.nodes[nid].containers)
        assert roots == [f"root:{graph.repo}"], f"expected exactly one root, got {roots}"
        bodies = self._bodies(graph)
        seen = set(roots)
        queue = list(roots)
        while queue:
            for member in bodies.get(queue.pop(), []):
                if member not in seen:
                    seen.add(member)
                    queue.append(member)
        orphaned = sorted(nid for nid in graph.nodes if nid not in seen)
        assert not orphaned, f"{len(orphaned)} nodes unreachable from root: {orphaned[:5]}"

    def _bodies(self, graph: BudgetWorkGraph) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for node_id in sorted(graph.nodes):
            for container in graph.nodes[node_id].containers:
                grouped.setdefault(container, []).append(node_id)
        return grouped

    def _assert_cohesion(self, graph: BudgetWorkGraph) -> None:
        for owner in sorted(graph.nodes):
            node = graph.nodes[owner]
            members = node.hidden_children
            if node.body_kind == "list" or len(members) <= 1:
                continue
            member_set = set(members)
            internal = sum(
                1
                for edge in graph.edges.values()
                if edge.source in member_set and edge.target in member_set
            )
            assert internal >= len(members) - 1, (
                f"{owner} cohesion gap: members={members} internal={internal}"
            )

from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph
from tracer.services.analysis.graph_ops import bodies_by_container


class ContainmentInvariants:
    def enforce_structure(self, graph: BudgetWorkGraph) -> None:
        self._assert_dag(graph)
        self._assert_total(graph)

    def enforce_bodies(self, graph: BudgetWorkGraph) -> None:
        self._drop_dangling(graph)
        self._assert_hidden_paths(graph)
        self._assert_reachable(graph)
        self._assert_cohesion(graph)

    def _drop_dangling(self, graph: BudgetWorkGraph) -> None:
        for edge in list(graph.edges.values()):
            if edge.source not in graph.nodes or edge.target not in graph.nodes:
                graph.remove_edge(edge)

    def _assert_hidden_paths(self, graph: BudgetWorkGraph) -> None:
        for key in sorted(graph.edges):
            edge = graph.edges[key]
            if not edge.hidden_path:
                continue
            for node_id in edge.hidden_path:
                node = graph.nodes.get(node_id)
                assert node is not None, f"hidden_path references missing node {node_id}"
                assert node.level >= 1, f"hidden_path node {node_id} is not hidden"
            for endpoint in (edge.source, edge.target):
                level = graph.nodes[endpoint].level
                assert level == 0, f"skeleton edge endpoint {endpoint} is level {level}"

    def _assert_reachable(self, graph: BudgetWorkGraph) -> None:
        reachable = graph.reachable()
        stranded = sorted(node_id for node_id in graph.nodes if node_id not in reachable)
        assert not stranded, f"{len(stranded)} nodes unreachable from any entry: {stranded[:5]}"

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
        bodies = bodies_by_container(graph.nodes)
        seen = set(roots)
        queue = list(roots)
        while queue:
            for member in bodies.get(queue.pop(), []):
                if member not in seen:
                    seen.add(member)
                    queue.append(member)
        orphaned = sorted(nid for nid in graph.nodes if nid not in seen)
        assert not orphaned, f"{len(orphaned)} nodes unreachable from root: {orphaned[:5]}"

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

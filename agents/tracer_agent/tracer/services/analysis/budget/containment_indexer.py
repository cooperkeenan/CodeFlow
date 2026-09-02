from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph

from shared.models.flow_graph import FlowNode


class ContainmentIndexer:
    def index(self, graph: BudgetWorkGraph, skeleton_ids: frozenset[str] = frozenset()) -> None:
        bodies = self._bodies(graph)
        self._assign_levels(graph, bodies, skeleton_ids)
        for owner in sorted(graph.nodes):
            self._assign_shape(graph, graph.nodes[owner], bodies.get(owner, []))
        for owner in sorted(graph.nodes):
            self._assign_kind(graph, owner, bodies.get(owner, []))

    def relevel(self, graph: BudgetWorkGraph, skeleton_ids: frozenset[str] = frozenset()) -> None:
        self._assign_levels(graph, self._bodies(graph), skeleton_ids)

    def _bodies(self, graph: BudgetWorkGraph) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for node_id in sorted(graph.nodes):
            for container in graph.nodes[node_id].containers:
                grouped.setdefault(container, []).append(node_id)
        return grouped

    def _assign_levels(
        self,
        graph: BudgetWorkGraph,
        bodies: dict[str, list[str]],
        skeleton_ids: frozenset[str],
    ) -> None:
        levels: dict[str, int] = {}
        queue = sorted(
            {nid for nid in graph.nodes if not graph.nodes[nid].containers} | skeleton_ids
        )
        for node_id in queue:
            levels[node_id] = 0
        while queue:
            current = queue.pop(0)
            for child in bodies.get(current, []):
                if child not in levels:
                    levels[child] = levels[current] + 1
                    queue.append(child)
        for node_id in sorted(graph.nodes):
            graph.nodes[node_id].level = levels.get(node_id, 0)

    def _assign_shape(self, graph: BudgetWorkGraph, owner: FlowNode, members: list[str]) -> None:
        if not members:
            owner.hidden_children = []
            owner.body_tails = []
            return
        member_set = set(members)
        adjacency: dict[str, list[str]] = {m: [] for m in members}
        for edge in graph.edges.values():
            if edge.source in member_set and edge.target in member_set:
                adjacency[edge.source].append(edge.target)
        owner.hidden_children = self._topo_sort(graph, members, adjacency)
        owner.body_tails = sorted(m for m in members if self._is_tail(graph, m, member_set))

    def _assign_kind(self, graph: BudgetWorkGraph, owner_id: str, members: list[str]) -> None:
        owner = graph.nodes[owner_id]
        if not members:
            owner.body_head = ""
            owner.body_kind = "flow"
            return
        member_set = set(members)
        subtree = self._subtree(graph, members)
        in_from_owner: set[str] = set()
        in_from_subtree: dict[str, int] = {m: 0 for m in members}
        for edge in graph.edges.values():
            if edge.target not in member_set:
                continue
            if edge.source == owner_id:
                in_from_owner.add(edge.target)
            elif edge.source in subtree:
                in_from_subtree[edge.target] += 1
        headless = [m for m in members if in_from_subtree[m] == 0 and m not in in_from_owner]
        if headless or not self._cohesive(graph, member_set):
            owner.body_kind = "list"
            owner.body_head = ""
        else:
            owner.body_kind = "flow"
            heads = sorted(in_from_owner)
            owner.body_head = heads[0] if heads else owner.hidden_children[0]

    def _cohesive(self, graph: BudgetWorkGraph, member_set: set[str]) -> bool:
        if len(member_set) <= 1:
            return True
        internal = sum(
            1
            for edge in graph.edges.values()
            if edge.source in member_set and edge.target in member_set
        )
        return internal >= len(member_set) - 1

    def _subtree(self, graph: BudgetWorkGraph, members: list[str]) -> set[str]:
        seen = set(members)
        queue = list(members)
        while queue:
            for child in graph.nodes[queue.pop()].hidden_children:
                if child not in seen:
                    seen.add(child)
                    queue.append(child)
        return seen

    def _is_tail(self, graph: BudgetWorkGraph, member: str, member_set: set[str]) -> bool:
        outs = graph.out_edges(member)
        if not outs:
            return True
        return any(edge.target not in member_set for edge in outs)

    def _topo_sort(
        self, graph: BudgetWorkGraph, members: list[str], adjacency: dict[str, list[str]]
    ) -> list[str]:
        remaining: dict[str, int] = {m: 0 for m in members}
        for m in members:
            for target in adjacency[m]:
                remaining[target] += 1
        ready = [m for m in members if remaining[m] == 0]
        order: list[str] = []
        while ready:
            ready.sort(key=lambda m: self._sort_key(graph, m))
            current = ready.pop(0)
            order.append(current)
            for target in adjacency[current]:
                remaining[target] -= 1
                if remaining[target] == 0:
                    ready.append(target)
        leftover = sorted((m for m in members if m not in order), key=lambda m: self._sort_key(graph, m))
        return order + leftover

    def _sort_key(self, graph: BudgetWorkGraph, node_id: str) -> tuple[str, int, str]:
        refs = graph.nodes[node_id].refs
        if refs:
            return (refs[0].file, refs[0].line, node_id)
        return ("", 0, node_id)

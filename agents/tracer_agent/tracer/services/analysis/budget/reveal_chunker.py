from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph

from shared.models.flow_graph import FlowNode


class RevealChunker:
    def __init__(self, max_reveal: int) -> None:
        self._max = max(max_reveal, 2)

    def chunk(
        self, graph: BudgetWorkGraph, hidden_children: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for owner in sorted(hidden_children):
            result.update(self._split(graph, owner, list(hidden_children[owner])))
        return result

    def _split(
        self, graph: BudgetWorkGraph, owner: str, kids: list[str]
    ) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        current = owner
        index = 0
        split = False
        while len(kids) > self._max:
            split = True
            head = kids[: self._max - 1]
            kids = kids[self._max - 1 :]
            more_id = f"more:{owner}:{index}"
            self._add_more(graph, owner, current, more_id, len(kids))
            graph.add_edge(current, more_id, "sequence")
            if head and head[-1] != current:
                graph.add_edge(head[-1], more_id, "sequence")
            piece = head + [more_id]
            out[current] = piece
            graph.nodes[current].body_kind = self._kind_for(graph, piece)
            current = more_id
            index += 1
        out[current] = kids
        if split:
            graph.nodes[current].body_kind = self._kind_for(graph, kids)
        return out

    def _add_more(
        self, graph: BudgetWorkGraph, owner: str, parent_id: str, more_id: str, remaining: int
    ) -> None:
        host = graph.nodes[owner]
        graph.nodes[more_id] = FlowNode(
            id=more_id,
            kind="step",
            lane=host.lane,
            label=f"+{remaining} more",
            badges=["folded"],
            folded_count=remaining,
            owner_fqn=host.owner_fqn,
            containers=[parent_id],
        )

    def _kind_for(self, graph: BudgetWorkGraph, members: list[str]) -> str:
        if len(members) <= 1:
            return "flow"
        member_set = set(members)
        internal = sum(
            1
            for edge in graph.edges.values()
            if edge.source in member_set and edge.target in member_set
        )
        return "flow" if internal >= len(members) - 1 else "list"

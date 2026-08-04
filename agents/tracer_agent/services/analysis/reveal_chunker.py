from services.analysis.budget_work_graph import BudgetWorkGraph
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
        while len(kids) > self._max:
            head = kids[: self._max - 1]
            kids = kids[self._max - 1 :]
            more_id = f"more:{owner}:{index}"
            self._add_more(graph, owner, current, more_id, len(kids))
            graph.add_edge(current, more_id, "sequence")
            if head and head[-1] != current:
                graph.add_edge(head[-1], more_id, "sequence")
            out[current] = head + [more_id]
            current = more_id
            index += 1
        out[current] = kids
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
            body_kind=host.body_kind,
        )

from shared.flow_endpoints.slice_graph import SliceGraph
from shared.models.flow_graph import FlowNode

RUN_PREFIX = "run:"
_MIN_RUN = 3


class RunCollapser:
    def __init__(self, min_run: int = _MIN_RUN, floor: int = 10) -> None:
        self._min = max(min_run, 2)
        self._floor = floor

    def collapse(self, graph: SliceGraph) -> None:
        for head_id in sorted(graph.keep):
            if head_id not in graph.keep or head_id == graph.root_id:
                continue
            run = self._run_from(graph, head_id)
            if len(run) < self._min:
                continue
            if len(graph.keep) - len(run) + 1 < self._floor:
                continue
            self._fold(graph, run)

    def _run_from(self, graph: SliceGraph, head_id: str) -> list[str]:
        if self._entered_mid_run(graph, head_id):
            return []
        run = [head_id]
        current = head_id
        while not graph.is_fork(current):
            successors = [s for s in graph.successors(current) if s in graph.keep]
            if len(successors) != 1:
                break
            nxt = successors[0]
            if nxt in run or graph.is_fork(nxt):
                break
            if len([p for p in graph.predecessors(nxt) if p in graph.keep]) != 1:
                break
            run.append(nxt)
            current = nxt
        return run

    def _entered_mid_run(self, graph: SliceGraph, node_id: str) -> bool:
        parents = [p for p in graph.predecessors(node_id) if p in graph.keep]
        if len(parents) != 1:
            return False
        parent = parents[0]
        if graph.is_fork(parent):
            return False
        return len([s for s in graph.successors(parent) if s in graph.keep]) == 1

    def _fold(self, graph: SliceGraph, run: list[str]) -> None:
        tail = graph.nodes[run[-1]]
        host = FlowNode(
            id=f"{RUN_PREFIX}{run[0]}",
            kind=tail.kind,
            lane=tail.lane,
            label=tail.label,
            llm_label=tail.llm_label,
            one_liner=tail.one_liner,
            refs=list(tail.refs[:1]),
            badges=["folded"],
            folded_count=len(run) - 1,
            owner_fqn=tail.owner_fqn,
            effect_kind=tail.effect_kind,
            effect_target=tail.effect_target,
        )
        graph.add_node(host)
        graph.absorb(set(run) | {host.id}, host.id)

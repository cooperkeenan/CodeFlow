from services.analysis.call_graph import CallGraph
from services.analysis.scc_index import SccIndex


class SccIndexBuilder:
    def build(self, graph: CallGraph) -> SccIndex:
        state = _TarjanState(graph)
        for node in graph.nodes:
            if node not in state.indices:
                state.run(node)
        members: dict[int, set[str]] = {}
        for node, scc in state.assignment.items():
            members.setdefault(scc, set()).add(node)
        return SccIndex(dict(state.assignment), {k: frozenset(v) for k, v in members.items()})


class _TarjanState:
    def __init__(self, graph: CallGraph) -> None:
        self._graph = graph
        self.indices: dict[str, int] = {}
        self.lowlink: dict[str, int] = {}
        self.on_stack: set[str] = set()
        self.stack: list[str] = []
        self.assignment: dict[str, int] = {}
        self._counter = 0
        self._next_scc = 0

    def run(self, start: str) -> None:
        work: list[tuple[str, list[str]]] = [(start, list(self._graph.successors(start)))]
        self._enter(start)
        while work:
            node, pending = work[-1]
            if pending:
                nxt = pending.pop()
                if nxt not in self.indices:
                    self._enter(nxt)
                    work.append((nxt, list(self._graph.successors(nxt))))
                elif nxt in self.on_stack:
                    self.lowlink[node] = min(self.lowlink[node], self.indices[nxt])
                continue
            self._close(node)
            work.pop()
            if work:
                parent = work[-1][0]
                self.lowlink[parent] = min(self.lowlink[parent], self.lowlink[node])

    def _enter(self, node: str) -> None:
        self.indices[node] = self.lowlink[node] = self._counter
        self._counter += 1
        self.stack.append(node)
        self.on_stack.add(node)

    def _close(self, node: str) -> None:
        if self.lowlink[node] != self.indices[node]:
            return
        while True:
            member = self.stack.pop()
            self.on_stack.discard(member)
            self.assignment[member] = self._next_scc
            if member == node:
                break
        self._next_scc += 1

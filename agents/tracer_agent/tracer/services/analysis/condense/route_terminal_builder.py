import ast

from tracer.models.flow_summary import FlowSummary
from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.condense.terminal_node_builder import TerminalNodeBuilder
from tracer.services.analysis.syntax.terminal_classifier import classify_terminal

_COMPLETES = "Completes"


class RouteTerminalBuilder:
    def __init__(
        self, index: ProjectIndex, acc: GraphAccumulator, nodes: TerminalNodeBuilder
    ) -> None:
        self._index = index
        self._acc = acc
        self._nodes = nodes

    def terminate(self, fqn: str, summary: FlowSummary) -> FlowSummary:
        record = self._index.functions.get(fqn)
        body = getattr(getattr(record, "body", None), "body", None)
        if not body:
            return summary
        last = body[-1]
        terminal = isinstance(last, (ast.Return, ast.Raise))
        if not terminal and classify_terminal(body) != "falls_through":
            return summary
        if self._ends_in_response(summary):
            return summary
        open_tails = self._open_tails(summary)
        if summary.head is not None and not open_tails:
            return summary
        node_id = f"ret:{fqn}:{last.lineno}"
        if node_id in summary.tails or node_id == summary.head:
            return summary
        node_id = self._nodes.emit(fqn, last, None if terminal else _COMPLETES)
        if summary.head is None:
            return FlowSummary(node_id, (node_id,), summary.recursive)
        for tail in open_tails:
            self._acc.connect(tail, node_id, "sequence")
        return FlowSummary(summary.head, (node_id,), summary.recursive)

    def _open_tails(self, summary: FlowSummary) -> tuple[str, ...]:
        nodes = self._acc.nodes()
        tails = summary.tails or ((summary.head,) if summary.head else ())
        return tuple(t for t in tails if nodes[t].kind != "outcome")

    def _ends_in_response(self, summary: FlowSummary) -> bool:
        nodes = self._acc.nodes()
        return any(
            nodes[t].kind == "effect" and nodes[t].effect_kind == "response"
            for t in summary.tails
            if t in nodes
        )

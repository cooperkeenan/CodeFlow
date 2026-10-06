import ast

from tracer.models.flow_summary import FlowSummary
from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer
from tracer.services.analysis.syntax.http_status_labels import status_call_label
from tracer.services.analysis.syntax.step_label_normalizer import normalize_label
from tracer.services.analysis.syntax.step_labels import node_label

from shared.models.flow_graph import SourceRef


class RouteTerminalBuilder:
    def __init__(
        self,
        index: ProjectIndex,
        acc: GraphAccumulator,
        labels: LabelSynthesizer,
        roots: ServiceRootResolver,
    ) -> None:
        self._index = index
        self._acc = acc
        self._labels = labels
        self._roots = roots

    def terminate(self, fqn: str, summary: FlowSummary) -> FlowSummary:
        record = self._index.functions.get(fqn)
        body = getattr(getattr(record, "body", None), "body", None)
        if not body:
            return summary
        last = body[-1]
        terminal = isinstance(last, (ast.Return, ast.Raise))
        if summary.head is not None and not terminal:
            return summary
        if self._ends_in_response(summary):
            return summary
        open_tails = self._open_tails(summary)
        if summary.head is not None and not open_tails:
            return summary
        node_id = f"ret:{fqn}:{last.lineno}"
        if node_id in (summary.tails or ()) or node_id == summary.head:
            return summary
        label = self._label(fqn, last) if terminal else self._labels.step_label([fqn])
        self._acc.upsert(
            node_id, "outcome", self._roots.root_of(fqn), label,
            refs=[SourceRef(file=record.span.file, line=last.lineno, end_line=last.end_lineno or last.lineno)],
        )
        self._acc.set_owner(node_id, fqn, [])
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

    def _label(self, fqn: str, stmt: ast.stmt) -> str:
        raw = node_label(stmt)
        if isinstance(stmt, ast.Raise):
            return normalize_label("raise", raw)
        value = stmt.value
        code = status_call_label(value) if isinstance(value, ast.Call) else None
        return f"return {code}" if code is not None else normalize_label("return", raw)

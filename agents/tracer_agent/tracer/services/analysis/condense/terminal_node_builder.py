import ast

from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.syntax.http_status_labels import status_call_label
from tracer.services.analysis.syntax.step_label_normalizer import normalize_label
from tracer.services.analysis.syntax.step_labels import node_label

from shared.models.flow_graph import SourceRef


class TerminalNodeBuilder:
    def __init__(
        self,
        index: ProjectIndex,
        acc: GraphAccumulator,
        roots: ServiceRootResolver,
        route_fqns: frozenset[str],
    ) -> None:
        self._index = index
        self._acc = acc
        self._roots = roots
        self._route_fqns = route_fqns

    def emit(self, fqn: str, stmt: ast.stmt, label: str | None = None) -> str:
        record = self._index.functions[fqn]
        node_id = f"ret:{fqn}:{stmt.lineno}"
        self._acc.upsert(
            node_id, "outcome", self._roots.root_of(fqn), f"{self._owner(fqn)}: {label or self.label_of(stmt)}",
            refs=[SourceRef(file=record.span.file, line=stmt.lineno, end_line=stmt.end_lineno or stmt.lineno)],
        )
        self._acc.set_owner(node_id, fqn, [])
        return node_id

    def close_arm(self, fqn: str, terminal_line: int, tails: list[str]) -> bool:
        if fqn not in self._route_fqns or not terminal_line:
            return False
        stmt = self._statement_at(fqn, terminal_line)
        if stmt is None:
            return False
        node_id = self.emit(fqn, stmt)
        nodes = self._acc.nodes()
        for tail in tails:
            if tail in nodes and nodes[tail].kind != "outcome":
                self._acc.connect(tail, node_id, "sequence")
        return True

    def label_of(self, stmt: ast.stmt) -> str:
        raw = node_label(stmt)
        if isinstance(stmt, ast.Raise):
            return normalize_label("raise", raw)
        value = getattr(stmt, "value", None)
        code = status_call_label(value) if isinstance(value, ast.Call) else None
        body = normalize_label("return", raw)
        return f"return {code} {body.removeprefix('return ')}" if code is not None else body

    @staticmethod
    def _owner(fqn: str) -> str:
        return ".".join(fqn.split(".")[-2:])

    def _statement_at(self, fqn: str, line: int) -> ast.stmt | None:
        record = self._index.functions.get(fqn)
        for node in ast.walk(record.body) if record is not None else ():
            if isinstance(node, (ast.Return, ast.Raise)) and node.lineno == line:
                return node
        return None

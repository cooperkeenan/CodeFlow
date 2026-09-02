import ast

from tracer.models.call_records import Arm
from tracer.models.index_records import FunctionRecord
from tracer.models.sites import DispatchSite
from tracer.services.analysis.contracts import DispatchDetectionContext
from tracer.services.analysis.syntax.call_expr_split import truncated_source
from tracer.services.analysis.syntax.selector_reads_extractor import selector_reads

from shared.models.flow_graph import SourceRef


class DynamicDetector:
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        sites: list[DispatchSite] = []
        for record in context.index.functions.values():
            for node in ast.walk(record.body):
                if not isinstance(node, ast.Call):
                    continue
                dynamic_key = self._dynamic_key(node)
                if dynamic_key is not None:
                    sites.append(self._build_site(record, node, dynamic_key))
        return tuple(sites)

    def _dynamic_key(self, node: ast.Call) -> ast.expr | None:
        func = node.func
        if isinstance(func, ast.Call) and isinstance(func.func, ast.Name) and func.func.id == "getattr":
            if len(func.args) >= 2 and not isinstance(func.args[1], ast.Constant):
                return func.args[1]
            return None
        if isinstance(func, ast.Subscript):
            base = func.value
            if isinstance(base, ast.Call) and isinstance(base.func, ast.Name) and base.func.id == "globals":
                slice_node = func.slice
                if not isinstance(slice_node, ast.Constant):
                    return slice_node
        return None

    def _build_site(self, record: FunctionRecord, call: ast.Call, key_node: ast.expr) -> DispatchSite:
        arms = self._hint_arms(key_node)
        return DispatchSite(
            id=f"{record.fqn}:{call.lineno}",
            owner=record.fqn,
            kind="dynamic",
            selector_source=truncated_source(call)[:120],
            selector_reads=selector_reads(call.func),
            arms=arms,
            reconverges=True,
            span=SourceRef(file=record.span.file, line=call.lineno, end_line=call.end_lineno or call.lineno),
        )

    def _hint_arms(self, key_node: ast.expr) -> tuple[Arm, ...]:
        if not isinstance(key_node, ast.JoinedStr):
            return ()
        prefix = self._literal_prefix(key_node)
        if prefix is None:
            return ()
        return (Arm(index=0, label_source=prefix, callsites=(), terminal="falls_through"),)

    def _literal_prefix(self, node: ast.JoinedStr) -> str | None:
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str) and part.value:
                return f"{part.value}*"
        return None

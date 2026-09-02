import ast

from tracer.models.call_records import Arm
from tracer.models.index_records import FunctionRecord, ProjectIndex
from tracer.models.sites import DispatchSite
from tracer.services.analysis.contracts import DispatchDetectionContext
from tracer.services.analysis.syntax.call_expr_split import truncated_source

from shared.models.flow_graph import SourceRef

_TableEntries = dict[str, str]


class TableDetector:
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        sites: list[DispatchSite] = []
        for module_fqn in context.index.modules:
            module_record = context.index.functions.get(f"{module_fqn}.<module>")
            if module_record is None:
                continue
            tables = self._tables(module_record, module_fqn, context.index)
            if not tables:
                continue
            for record in context.index.functions.values():
                if record.module == module_fqn:
                    sites.extend(self._lookups(record, tables))
        return tuple(sites)

    def _tables(self, module_record: FunctionRecord, module_fqn: str, index: ProjectIndex) -> dict[str, _TableEntries]:
        tables: dict[str, _TableEntries] = {}
        for stmt in module_record.body.body:
            if not (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Dict)):
                continue
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                continue
            entries = self._entries(stmt.value, module_fqn, index)
            if entries:
                tables[stmt.targets[0].id] = entries
        return tables

    def _entries(self, node: ast.Dict, module_fqn: str, index: ProjectIndex) -> _TableEntries | None:
        entries: _TableEntries = {}
        for key, value in zip(node.keys, node.values):
            if key is None or not isinstance(key, ast.Constant):
                return None
            target = self._resolve_value(value, module_fqn, index)
            if target is None:
                return None
            entries[repr(key.value)] = target
        return entries if entries else None

    def _resolve_value(self, node: ast.expr, module_fqn: str, index: ProjectIndex) -> str | None:
        if not isinstance(node, ast.Name):
            return None
        resolved = index.resolve(module_fqn, node.id)
        if resolved is not None and (resolved in index.functions or resolved in index.classes):
            return resolved
        return None

    def _lookups(self, record: FunctionRecord, tables: dict[str, _TableEntries]) -> list[DispatchSite]:
        sites: list[DispatchSite] = []
        for node in ast.walk(record.body):
            if not isinstance(node, ast.Call):
                continue
            table_name = self._lookup_table_name(node)
            if table_name is None or table_name not in tables:
                continue
            sites.append(self._build_site(record, node, tables[table_name]))
        return sites

    def _lookup_table_name(self, node: ast.Call) -> str | None:
        func = node.func
        if isinstance(func, ast.Subscript) and isinstance(func.value, ast.Name):
            return func.value.id
        if (
            isinstance(func, ast.Call)
            and isinstance(func.func, ast.Attribute)
            and func.func.attr == "get"
            and isinstance(func.func.value, ast.Name)
            and func.args
        ):
            return func.func.value.id
        return None

    def _build_site(self, record: FunctionRecord, call: ast.Call, entries: _TableEntries) -> DispatchSite:
        arms = tuple(
            Arm(index=i, label_source=key, callsites=(), terminal="falls_through")
            for i, key in enumerate(entries)
        )
        return DispatchSite(
            id=f"{record.fqn}:{call.lineno}",
            owner=record.fqn,
            kind="table",
            selector_source=truncated_source(call)[:120],
            selector_reads=(),
            arms=arms,
            reconverges=True,
            span=SourceRef(file=record.span.file, line=call.lineno, end_line=call.end_lineno or call.lineno),
        )

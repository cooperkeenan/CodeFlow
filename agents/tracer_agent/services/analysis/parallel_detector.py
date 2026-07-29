import ast

from models.call_site import CallSite
from models.parallel_site import ParallelSite
from models.project_index import ProjectIndex
from shared.models.flow_graph import SourceRef

_FANOUT_ATTRS = frozenset({"gather", "create_task", "TaskGroup"})


class ParallelDetector:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index

    def detect(self, callsites: tuple[CallSite, ...]) -> tuple[ParallelSite, ...]:
        by_caller: dict[str, list[CallSite]] = {}
        for site in callsites:
            by_caller.setdefault(site.caller, []).append(site)
        sites: list[ParallelSite] = []
        for record in self._index.functions.values():
            lines = self._fanout_lines(record.body)
            for line in sorted(lines):
                callees = self._callees(by_caller.get(record.fqn, []), line)
                if callees:
                    sites.append(self._build(record.fqn, record.span.file, line, callees))
        return tuple(sites)

    def _fanout_lines(self, body: ast.AST) -> set[int]:
        lines: set[int] = set()
        for node in ast.walk(body):
            if isinstance(node, ast.Call) and self._is_fanout(node.func):
                lines.add(node.lineno)
        return lines

    def _is_fanout(self, func: ast.expr) -> bool:
        return isinstance(func, ast.Attribute) and func.attr in _FANOUT_ATTRS

    def _callees(self, sites: list[CallSite], line: int) -> tuple[str, ...]:
        found: list[str] = []
        for site in sites:
            if site.line != line:
                continue
            for target in site.targets:
                if target.fqn in self._index.functions and target.fqn not in found:
                    found.append(target.fqn)
        return tuple(found)

    def _build(self, owner: str, file: str, line: int, callees: tuple[str, ...]) -> ParallelSite:
        return ParallelSite(
            id=f"par:{owner}:{line}",
            owner=owner,
            line=line,
            callees=callees,
            span=SourceRef(file=file, line=line, end_line=line),
        )

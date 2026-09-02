import ast
from collections.abc import Mapping

from tracer.models.call_records import ControlFrame
from tracer.models.sites import EffectSite
from tracer.services.analysis.effects.effect_matcher import CallEffectMatcher

from shared.models.flow_graph import EffectKind


class EffectVisitor(ast.NodeVisitor):
    def __init__(
        self,
        owner_fqn: str,
        ext_roots_by_line: Mapping[int, frozenset[str]],
        matcher: CallEffectMatcher,
        constants: Mapping[str, str],
        response_target: str | None,
    ) -> None:
        self._owner = owner_fqn
        self._ext_roots = ext_roots_by_line
        self._matcher = matcher
        self._constants = constants
        self._response_target = response_target
        self._stack: list[ControlFrame] = []
        self.effects: list[EffectSite] = []

    def visit_Call(self, node: ast.Call) -> None:
        roots = self._ext_roots.get(node.lineno)
        if roots:
            match = self._matcher.match(node, roots, self._constants)
            if match is not None:
                self._emit(match.kind, match.target, match.method, node.lineno)
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        if self._response_target is not None:
            self._emit("response", self._response_target, "", node.lineno)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        site_id = self._site_id(node.lineno)
        self._frame("if", site_id, 0, node.body)
        if node.orelse:
            self._frame("if", site_id, 1, node.orelse)

    def visit_Match(self, node: ast.Match) -> None:
        self.visit(node.subject)
        site_id = self._site_id(node.lineno)
        for index, case in enumerate(node.cases):
            self._frame("match", site_id, index, case.body)

    def visit_Try(self, node: ast.Try) -> None:
        site_id = self._site_id(node.lineno)
        self._frame("try", site_id, 0, node.body)
        for index, handler in enumerate(node.handlers):
            self._frame("try", site_id, index + 1, handler.body)
        if node.orelse:
            self._frame("try", site_id, len(node.handlers) + 1, node.orelse)
        if node.finalbody:
            self._frame("try", site_id, len(node.handlers) + 2, node.finalbody)

    def visit_For(self, node: ast.For) -> None:
        self._loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._loop(node)

    def visit_With(self, node: ast.With) -> None:
        self._with(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._with(node)

    def _loop(self, node: ast.For | ast.AsyncFor | ast.While) -> None:
        site_id = self._site_id(node.lineno)
        self._frame("loop", site_id, 0, node.body)
        if node.orelse:
            self._frame("loop", site_id, 1, node.orelse)

    def _with(self, node: ast.With | ast.AsyncWith) -> None:
        site_id = self._site_id(node.lineno)
        for item in node.items:
            self.visit(item.context_expr)
        self._frame("with", site_id, 0, node.body)

    def _frame(self, kind: str, site_id: str, arm_index: int, stmts: list[ast.stmt]) -> None:
        self._stack.append(ControlFrame(kind=kind, site_id=site_id, arm_index=arm_index))
        for stmt in stmts:
            self.visit(stmt)
        self._stack.pop()

    def _site_id(self, line: int) -> str:
        return f"{self._owner}:{line}"

    def _emit(self, kind: EffectKind, target: str, method: str, line: int) -> None:
        self.effects.append(
            EffectSite(
                id=f"eff:{self._owner}:{line}",
                owner=self._owner,
                kind=kind,
                target=target,
                method=method,
                line=line,
                context=tuple(self._stack),
            )
        )

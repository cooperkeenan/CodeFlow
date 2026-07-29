import ast

from models.call_site import CallSite
from models.control_frame import ControlFrame
from models.project_index import ProjectIndex
from models.resolved_target import ResolvedTarget
from services.analysis.call_expr_split import truncated_source
from services.analysis.call_target_resolver import CallTargetResolver

_ATOMIC = (ast.Constant, ast.Call)


class CallSiteVisitor(ast.NodeVisitor):
    def __init__(self, owner_fqn: str, resolver: CallTargetResolver, index: ProjectIndex) -> None:
        self._owner_fqn = owner_fqn
        self._resolver = resolver
        self._index = index
        self._stack: list[ControlFrame] = []
        self.sites: list[CallSite] = []

    def visit_Call(self, node: ast.Call) -> None:
        targets = self._resolver.resolve_call(node.func)
        self.sites.append(self._build_site(node, targets))
        self._emit_callbacks(node, targets)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        site_id = self._site_id(node.lineno)
        self._visit_frame("if", site_id, 0, node.body)
        if node.orelse:
            self._visit_frame("if", site_id, 1, node.orelse)

    def visit_Match(self, node: ast.Match) -> None:
        self.visit(node.subject)
        site_id = self._site_id(node.lineno)
        for i, case in enumerate(node.cases):
            self._visit_frame("match", site_id, i, case.body)

    def visit_Try(self, node: ast.Try) -> None:
        site_id = self._site_id(node.lineno)
        self._visit_frame("try", site_id, 0, node.body)
        for i, handler in enumerate(node.handlers):
            self._visit_frame("try", site_id, i + 1, handler.body)
        if node.orelse:
            self._visit_frame("try", site_id, len(node.handlers) + 1, node.orelse)
        if node.finalbody:
            self._visit_frame("try", site_id, len(node.handlers) + 2, node.finalbody)

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node)

    def visit_With(self, node: ast.With) -> None:
        self._visit_with(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_with(node)

    def _visit_loop(self, node: ast.For | ast.AsyncFor | ast.While) -> None:
        site_id = self._site_id(node.lineno)
        self._visit_frame("loop", site_id, 0, node.body)
        if node.orelse:
            self._visit_frame("loop", site_id, 1, node.orelse)

    def _visit_with(self, node: ast.With | ast.AsyncWith) -> None:
        site_id = self._site_id(node.lineno)
        for item in node.items:
            self.visit(item.context_expr)
        self._visit_frame("with", site_id, 0, node.body)

    def _visit_frame(self, kind: str, site_id: str, arm_index: int, stmts: list[ast.stmt]) -> None:
        self._stack.append(ControlFrame(kind=kind, site_id=site_id, arm_index=arm_index))
        for stmt in stmts:
            self.visit(stmt)
        self._stack.pop()

    def _site_id(self, line: int) -> str:
        return f"{self._owner_fqn}:{line}"

    def _in_loop(self) -> bool:
        return any(frame.kind == "loop" for frame in self._stack)

    def _build_site(self, node: ast.Call, targets: tuple[ResolvedTarget, ...]) -> CallSite:
        return CallSite(
            caller=self._owner_fqn,
            line=node.lineno,
            targets=targets,
            context=tuple(self._stack),
            in_loop=self._in_loop(),
            call_source=truncated_source(node),
        )

    def _emit_callbacks(self, node: ast.Call, targets: tuple[ResolvedTarget, ...]) -> None:
        receiver = targets[0].fqn if targets else self._owner_fqn
        for arg in list(node.args) + [kw.value for kw in node.keywords]:
            if isinstance(arg, _ATOMIC):
                continue
            resolved = self._resolver.resolve_bare_reference(arg)
            if resolved is None or resolved not in self._index.functions:
                continue
            self.sites.append(
                CallSite(
                    caller=receiver,
                    line=node.lineno,
                    targets=(ResolvedTarget(resolved, "inferred"),),
                    context=tuple(self._stack),
                    in_loop=self._in_loop(),
                    call_source=truncated_source(arg),
                )
            )

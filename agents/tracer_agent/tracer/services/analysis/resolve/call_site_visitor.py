import ast

from tracer.models.call_records import CallSite, ResolvedTarget
from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.resolve.call_target_resolver import CallTargetResolver
from tracer.services.analysis.syntax.call_expr_split import truncated_source
from tracer.services.analysis.syntax.control_frame_visitor import ControlFrameVisitor

_ATOMIC = (ast.Constant, ast.Call)


class CallSiteVisitor(ControlFrameVisitor):
    def __init__(self, owner_fqn: str, resolver: CallTargetResolver, index: ProjectIndex) -> None:
        super().__init__(owner_fqn)
        self._resolver = resolver
        self._index = index
        self.sites: list[CallSite] = []

    def visit_Call(self, node: ast.Call) -> None:
        targets = self._resolver.resolve_call(node.func)
        self.sites.append(self._build_site(node, targets))
        self._emit_callbacks(node, targets)
        self.generic_visit(node)

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

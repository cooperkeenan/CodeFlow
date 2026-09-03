import ast
from collections.abc import Mapping

from tracer.models.sites import EffectSite
from tracer.services.analysis.effects.effect_matcher import CallEffectMatcher
from tracer.services.analysis.syntax.control_frame_visitor import ControlFrameVisitor

from shared.models.flow_graph import EffectKind


class EffectVisitor(ControlFrameVisitor):
    def __init__(
        self,
        owner_fqn: str,
        ext_roots_by_line: Mapping[int, frozenset[str]],
        matcher: CallEffectMatcher,
        constants: Mapping[str, str],
        response_target: str | None,
    ) -> None:
        super().__init__(owner_fqn)
        self._ext_roots = ext_roots_by_line
        self._matcher = matcher
        self._constants = constants
        self._response_target = response_target
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

    def _emit(self, kind: EffectKind, target: str, method: str, line: int) -> None:
        self.effects.append(
            EffectSite(
                id=f"eff:{self._owner_fqn}:{line}",
                owner=self._owner_fqn,
                kind=kind,
                target=target,
                method=method,
                line=line,
                context=tuple(self._stack),
            )
        )

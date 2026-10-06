import ast
from dataclasses import replace

from tracer.models.call_records import Arm
from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.resolve.module_scope_resolver import ModuleScopeResolver
from tracer.services.analysis.resolve.mro_method_finder import MroMethodFinder
from tracer.services.analysis.syntax.terminal_classifier import classify_terminal

_VERBS = ("get", "post", "put", "patch", "delete")


class DjangoViewResolver:
    def __init__(self, index: ProjectIndex, mro: MroMethodFinder) -> None:
        self._index = index
        self._mro = mro

    def arms_for(
        self, full_path: str, view: ast.expr, scope: ModuleScopeResolver, start: int
    ) -> list[Arm]:
        inner, wrappers = self._unwrap(view, scope)
        arms = self._resolve(full_path, inner, scope, start)
        if not arms and inner is not view:
            return self._resolve(full_path, view, scope, start)
        return [replace(arm, wrappers=wrappers) for arm in arms]

    def _unwrap(self, view: ast.expr, scope: ModuleScopeResolver) -> tuple[ast.expr, tuple[str, ...]]:
        wrappers: list[str] = []
        while isinstance(view, ast.Call) and view.args and not self._is_as_view(view):
            fqn = scope.resolve_node(view.func)
            if fqn is not None and fqn in self._index.functions:
                wrappers.append(fqn)
            view = view.args[0]
        return view, tuple(wrappers)

    @staticmethod
    def _is_as_view(call: ast.Call) -> bool:
        return isinstance(call.func, ast.Attribute) and call.func.attr == "as_view"

    def _resolve(self, full_path: str, view: ast.expr, scope: ModuleScopeResolver, start: int) -> list[Arm]:
        if isinstance(view, ast.Call) and self._is_as_view(view):
            class_fqn = scope.resolve_node(view.func.value)
            if class_fqn is None or class_fqn not in self._index.classes:
                return []
            return self._cbv_arms(full_path, class_fqn, start)
        handler_fqn = scope.resolve_node(view)
        if handler_fqn is None or handler_fqn not in self._index.functions:
            return []
        return [self._make_arm(start, "any", full_path, handler_fqn)]

    def _cbv_arms(self, full_path: str, class_fqn: str, start: int) -> list[Arm]:
        found = [(verb, fqn) for verb in _VERBS if (fqn := self._mro.find_project_method(class_fqn, verb))]
        if not found:
            dispatch = self._mro.find_project_method(class_fqn, "dispatch")
            if dispatch is not None:
                found = [("any", dispatch)]
        return [self._make_arm(start + i, verb, full_path, fqn) for i, (verb, fqn) in enumerate(found)]

    def _make_arm(self, position: int, verb: str, full_path: str, handler_fqn: str) -> Arm:
        record = self._index.functions[handler_fqn]
        return Arm(
            index=position,
            label_source=f"{verb.upper()} {full_path}",
            callsites=(),
            terminal=classify_terminal(record.body.body),
            handler_fqn=handler_fqn,
        )

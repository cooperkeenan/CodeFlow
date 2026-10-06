import ast

from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.resolve.module_scope_resolver import ModuleScopeResolver
from tracer.services.analysis.resolve.mro_method_finder import MroMethodFinder
from tracer.services.analysis.syntax.types import local_names_of

_VERBS = ("get", "post", "put", "patch", "delete")


class DelegationResolver:
    def __init__(self, index: ProjectIndex, mro: MroMethodFinder) -> None:
        self._index = index
        self._mro = mro
        self._scopes: dict[str, ModuleScopeResolver] = {}

    def resolve(self, handler_fqn: str) -> str | None:
        record = self._index.functions.get(handler_fqn)
        if record is None:
            return None
        call = self._sole_return_call(getattr(record.body, "body", []))
        scope = self._scope(record.module)
        if call is None or scope is None:
            return None
        inner = call.func
        if isinstance(inner, ast.Call) and self._is_as_view(inner):
            target = self._cbv_method(scope.resolve_node(inner.func.value))
        else:
            target = scope.resolve_node(call)
        if target is None or target == handler_fqn or target not in self._index.functions:
            return None
        return target

    def _sole_return_call(self, body: list[ast.stmt]) -> ast.Call | None:
        stmts = list(body)
        first = stmts[0] if stmts else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            stmts = stmts[1:]
        if len(stmts) != 1 or not isinstance(stmts[0], ast.Return):
            return None
        value = stmts[0].value
        return value if isinstance(value, ast.Call) else None

    @staticmethod
    def _is_as_view(call: ast.Call) -> bool:
        return isinstance(call.func, ast.Attribute) and call.func.attr == "as_view"

    def _cbv_method(self, class_fqn: str | None) -> str | None:
        if class_fqn is None or class_fqn not in self._index.classes:
            return None
        for verb in (*_VERBS, "dispatch"):
            found = self._mro.find_project_method(class_fqn, verb)
            if found is not None:
                return found
        return None

    def _scope(self, module_fqn: str) -> ModuleScopeResolver | None:
        if module_fqn not in self._scopes:
            module = self._index.modules.get(module_fqn)
            if module is None:
                return None
            self._scopes[module_fqn] = ModuleScopeResolver(
                module.bindings, local_names_of(module), module_fqn, self._index
            )
        return self._scopes[module_fqn]

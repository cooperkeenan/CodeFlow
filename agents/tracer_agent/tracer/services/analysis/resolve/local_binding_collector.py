import ast

from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.resolve.attribute_path_resolver import (
    AttributePathResolver,
)
from tracer.services.analysis.resolve.module_scope_resolver import ModuleScopeResolver
from tracer.services.analysis.resolve.self_expr_type_resolver import (
    SelfExprTypeResolver,
)
from tracer.services.analysis.syntax.call_expr_split import (
    split_call_target,
    unwrap_await,
)
from tracer.services.analysis.syntax.types import literal_type_hint, normalize_type


class LocalBindingCollector:
    def __init__(self, attribute_path: AttributePathResolver, index: ProjectIndex) -> None:
        self._attribute_path = attribute_path
        self._index = index

    def collect(
        self, body: ast.AST, scope: ModuleScopeResolver, self_types: SelfExprTypeResolver | None = None
    ) -> dict[str, str]:
        bindings: dict[str, str] = {}
        for node in ast.walk(body):
            target, value = self._simple_assign(node)
            if target is None or value is None:
                continue
            resolved = self._resolve_value(value, bindings, scope, self_types)
            if resolved is not None:
                bindings[target] = resolved
        return bindings

    def _resolve_value(
        self, value: ast.expr, bindings_so_far: dict[str, str], scope: ModuleScopeResolver,
        self_types: SelfExprTypeResolver | None,
    ) -> str | None:
        resolved = scope.resolve_node(value) or literal_type_hint(value)
        if resolved is not None:
            return resolved
        if self_types is not None:
            resolved = self_types.value_type_of(value)
            if resolved is not None:
                return resolved
        unwrapped = unwrap_await(value)
        if isinstance(unwrapped, ast.Call):
            root, chain = split_call_target(unwrapped.func)
            if root is not None and root in bindings_so_far:
                return self._call_value_type(bindings_so_far[root], chain)
        return None

    def _call_value_type(self, base: str, chain: list[str]) -> str | None:
        if not chain:
            return base
        result = self._attribute_path.resolve(base, chain)
        if not result:
            return None
        fqn = result[0].fqn
        if fqn.startswith("ext:"):
            return fqn
        record = self._index.functions.get(fqn)
        if record is not None and record.returns is not None:
            return normalize_type(record.returns, self._index)
        return None

    def _simple_assign(self, node: ast.AST) -> tuple[str | None, ast.expr | None]:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            return node.targets[0].id, node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            return node.target.id, node.value
        if isinstance(node, ast.withitem) and isinstance(node.optional_vars, ast.Name):
            return node.optional_vars.id, node.context_expr
        return None, None

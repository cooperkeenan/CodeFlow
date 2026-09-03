import ast

from tracer.models.call_records import ResolvedTarget
from tracer.models.index_records import FunctionRecord, ProjectIndex
from tracer.services.analysis.resolve.attribute_path_resolver import (
    AttributePathResolver,
)
from tracer.services.analysis.resolve.indexes import UniqueNameIndex
from tracer.services.analysis.resolve.module_scope_resolver import ModuleScopeResolver
from tracer.services.analysis.resolve.self_call_resolver import SelfCallResolver
from tracer.services.analysis.syntax.call_expr_split import (
    split_call_target,
    split_chain_base,
)
from tracer.services.analysis.syntax.types import literal_type_hint

_SELF_ROOTS = {"self", "cls"}


class CallTargetResolver:
    def __init__(
        self,
        owner: FunctionRecord,
        scope: ModuleScopeResolver,
        local_bindings: dict[str, str],
        attribute_path: AttributePathResolver,
        self_resolver: SelfCallResolver,
        unique_names: UniqueNameIndex,
        index: ProjectIndex,
    ) -> None:
        self._owner = owner
        self._scope = scope
        self._local_bindings = local_bindings
        self._attribute_path = attribute_path
        self._self_resolver = self_resolver
        self._unique_names = unique_names
        self._index = index

    def resolve_call(self, func_node: ast.expr) -> tuple[ResolvedTarget, ...]:
        return self._ladder(func_node)

    def resolve_bare_reference(self, node: ast.expr) -> str | None:
        result = self._ladder(node)
        return result[0].fqn if result else None

    def _ladder(self, func_node: ast.expr) -> tuple[ResolvedTarget, ...]:
        root, chain = split_call_target(func_node)
        if root is None:
            return self._resolve_call_rooted_chain(func_node)
        if root in _SELF_ROOTS and self._owner.cls is not None:
            outcome = self._self_resolver.resolve(self._owner.cls, chain)
            if outcome is not None:
                return outcome
        else:
            if root in self._local_bindings:
                result = self._from_base(self._local_bindings[root], chain)
                if result is not None:
                    return result
            resolved = self._scope.resolve_node(func_node)
            if resolved is not None:
                return (ResolvedTarget(resolved, "resolved"),)
        return self._infer_or_dynamic(root, chain)

    def _resolve_call_rooted_chain(self, func_node: ast.expr) -> tuple[ResolvedTarget, ...]:
        base_node, chain = split_chain_base(func_node)
        inner_type = literal_type_hint(base_node)
        if inner_type is None and isinstance(base_node, ast.Call):
            inner_type = self._value_type_of(self._ladder(base_node.func))
        if inner_type is not None:
            result = self._from_base(inner_type, chain)
            if result is not None:
                return result
        return ()

    def _value_type_of(self, targets: tuple[ResolvedTarget, ...]) -> str | None:
        if not targets:
            return None
        fqn = targets[0].fqn
        if fqn.startswith("ext:") or fqn in self._index.classes:
            return fqn
        record = self._index.functions.get(fqn)
        return record.returns if record is not None else None

    def _from_base(self, base: str, chain: list[str]) -> tuple[ResolvedTarget, ...] | None:
        if not chain:
            return (ResolvedTarget(base, "resolved"),)
        return self._attribute_path.resolve(base, chain)

    def _infer_or_dynamic(self, root: str, chain: list[str]) -> tuple[ResolvedTarget, ...]:
        name = chain[-1] if chain else root
        unique = self._unique_names.resolve(name)
        return (ResolvedTarget(unique, "inferred"),) if unique is not None else ()

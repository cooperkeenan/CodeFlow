import ast

from models.function_record import FunctionRecord
from models.project_index import ProjectIndex
from models.resolved_target import ResolvedTarget
from services.analysis.attribute_path_resolver import AttributePathResolver
from services.analysis.call_expr_split import split_call_target, split_chain_base
from services.analysis.literal_type_hint import literal_type_hint
from services.analysis.module_scope_resolver import ModuleScopeResolver
from services.analysis.self_call_resolver import SelfCallResolver
from services.analysis.tier_counter import TierCounter
from services.analysis.unique_name_index import UniqueNameIndex

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
        tier_counter: TierCounter,
        index: ProjectIndex,
    ) -> None:
        self._owner = owner
        self._scope = scope
        self._local_bindings = local_bindings
        self._attribute_path = attribute_path
        self._self_resolver = self_resolver
        self._unique_names = unique_names
        self._tier_counter = tier_counter
        self._index = index

    def resolve_call(self, func_node: ast.expr) -> tuple[ResolvedTarget, ...]:
        result, tier = self._ladder(func_node)
        self._tier_counter.record(tier, self._is_ext(result))
        return result

    def resolve_bare_reference(self, node: ast.expr) -> str | None:
        result, _ = self._ladder(node)
        return result[0].fqn if result else None

    def _ladder(self, func_node: ast.expr) -> tuple[tuple[ResolvedTarget, ...], int]:
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
                    return result, 1
            resolved = self._scope.resolve_node(func_node)
            if resolved is not None:
                return (ResolvedTarget(resolved, "resolved"),), 2
        return self._infer_or_dynamic(root, chain)

    def _resolve_call_rooted_chain(self, func_node: ast.expr) -> tuple[tuple[ResolvedTarget, ...], int]:
        base_node, chain = split_chain_base(func_node)
        inner_type = literal_type_hint(base_node)
        if inner_type is None and isinstance(base_node, ast.Call):
            inner_result, _ = self._ladder(base_node.func)
            inner_type = self._value_type_of(inner_result)
        if inner_type is not None:
            result = self._from_base(inner_type, chain)
            if result is not None:
                return result, 2
        return (), 7

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

    def _infer_or_dynamic(self, root: str, chain: list[str]) -> tuple[tuple[ResolvedTarget, ...], int]:
        name = chain[-1] if chain else root
        unique = self._unique_names.resolve(name)
        if unique is not None:
            return (ResolvedTarget(unique, "inferred"),), 6
        return (), 7

    def _is_ext(self, targets: tuple[ResolvedTarget, ...]) -> bool:
        return any(t.fqn.startswith("ext:") for t in targets)

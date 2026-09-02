import ast

from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.resolve.self_call_resolver import SelfCallResolver
from tracer.services.analysis.syntax.call_expr_split import (
    split_call_target,
    unwrap_await,
)
from tracer.services.analysis.syntax.types import normalize_type

_SELF_ROOTS = {"self", "cls"}


class SelfExprTypeResolver:
    def __init__(self, owner_cls: str | None, self_resolver: SelfCallResolver, index: ProjectIndex) -> None:
        self._owner_cls = owner_cls
        self._self_resolver = self_resolver
        self._index = index

    def value_type_of(self, node: ast.expr) -> str | None:
        unwrapped = unwrap_await(node)
        if not isinstance(unwrapped, ast.Call) or self._owner_cls is None:
            return None
        root, chain = split_call_target(unwrapped.func)
        if root not in _SELF_ROOTS:
            return None
        outcome = self._self_resolver.resolve(self._owner_cls, chain)
        if outcome is None or not outcome[0]:
            return None
        fqn = outcome[0][0].fqn
        if fqn.startswith("ext:"):
            return fqn
        record = self._index.functions.get(fqn)
        if record is not None and record.returns is not None:
            return normalize_type(record.returns, self._index)
        return None

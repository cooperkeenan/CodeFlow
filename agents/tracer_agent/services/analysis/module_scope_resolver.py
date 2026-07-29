import ast
import builtins
from collections.abc import Mapping

from models.project_index import ProjectIndex
from services.analysis.call_expr_split import split_call_target, unwrap_await

_BUILTIN_NAMES = frozenset(vars(builtins))


class ModuleScopeResolver:
    def __init__(
        self,
        bindings: Mapping[str, str],
        local_names: frozenset[str],
        module_fqn: str,
        index: ProjectIndex,
    ) -> None:
        self._bindings = bindings
        self._local_names = local_names
        self._module_fqn = module_fqn
        self._index = index

    def resolve_node(self, node: ast.expr) -> str | None:
        unwrapped = unwrap_await(node)
        target = unwrapped.func if isinstance(unwrapped, ast.Call) else unwrapped
        root, chain = split_call_target(target)
        if root is None:
            return None
        return self.resolve_root(root, chain)

    def resolve_root(self, root: str, chain: list[str]) -> str | None:
        if root in self._local_names:
            base = self._index.resolve(self._module_fqn, root)
        else:
            base = self._bindings.get(root)
            if base is None:
                return "ext:builtins" if not chain and root in _BUILTIN_NAMES else None
        if base is None:
            return None
        if base.startswith("ext:"):
            return base
        if base in self._index.modules:
            return self._index.resolve(base, chain[0]) if chain else None
        joined = ".".join([base, *chain]) if chain else base
        if joined in self._index.functions or joined in self._index.classes:
            return joined
        return base if not chain else None

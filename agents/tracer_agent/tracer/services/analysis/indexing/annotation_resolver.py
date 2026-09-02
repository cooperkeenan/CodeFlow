import ast
from collections.abc import Mapping


class AnnotationResolver:
    def __init__(self, bindings: Mapping[str, str], local_names: frozenset[str], module_fqn: str) -> None:
        self._bindings = bindings
        self._local_names = local_names
        self._module_fqn = module_fqn

    def resolve(self, node: ast.expr | None) -> str | None:
        if node is None:
            return None
        target = node.func if isinstance(node, ast.Call) else node
        root, chain = self._split(target)
        if root is None:
            return ast.unparse(node)
        if root in self._local_names:
            return self._joined(f"{self._module_fqn}.{root}", chain)
        bound = self._bindings.get(root)
        if bound is not None:
            if bound.startswith("ext:"):
                return bound
            return self._joined(bound, chain)
        return ast.unparse(node)

    def _joined(self, base: str, chain: list[str]) -> str:
        return ".".join([base, *chain]) if chain else base

    def _split(self, node: ast.expr) -> tuple[str | None, list[str]]:
        chain: list[str] = []
        current = node
        while isinstance(current, ast.Attribute):
            chain.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            chain.reverse()
            return current.id, chain
        return None, []

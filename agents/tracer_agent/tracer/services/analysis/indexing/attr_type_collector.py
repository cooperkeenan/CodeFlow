import ast
from collections.abc import Mapping

from tracer.services.analysis.indexing.annotation_resolver import AnnotationResolver

_SKIP_PARAMS = {"self", "cls"}


class AttrTypeCollector:
    def collect(self, class_node: ast.ClassDef, resolver: AnnotationResolver) -> Mapping[str, str]:
        attr_types: dict[str, str] = {}
        for stmt in class_node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                resolved = resolver.resolve(stmt.annotation)
                if resolved is not None:
                    attr_types[stmt.target.id] = resolved
        init_node = self._find_init(class_node)
        if init_node is not None:
            attr_types.update(self._from_init(init_node, resolver))
        return dict(sorted(attr_types.items()))

    def _find_init(self, class_node: ast.ClassDef) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        for stmt in class_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "__init__":
                return stmt
        return None

    def _from_init(
        self, init_node: ast.FunctionDef | ast.AsyncFunctionDef, resolver: AnnotationResolver
    ) -> Mapping[str, str]:
        params = init_node.args.posonlyargs + init_node.args.args + init_node.args.kwonlyargs
        param_types = {
            arg.arg: resolver.resolve(arg.annotation)
            for arg in params
            if arg.arg not in _SKIP_PARAMS and arg.annotation is not None
        }
        attrs: dict[str, str] = {}
        for node in ast.walk(init_node):
            attr = self._self_attr(node)
            if attr is None:
                continue
            name, value = attr
            if isinstance(node, ast.AnnAssign):
                resolved = resolver.resolve(node.annotation)
                if resolved is not None:
                    attrs[name] = resolved
            elif isinstance(value, ast.Name) and value.id in param_types:
                resolved = param_types[value.id]
                if resolved is not None:
                    attrs[name] = resolved
        return attrs

    def _self_attr(self, node: ast.AST) -> tuple[str, ast.expr | None] | None:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if self._is_self_attr(target):
                return target.attr, node.value
        if isinstance(node, ast.AnnAssign) and self._is_self_attr(node.target):
            return node.target.attr, node.value
        return None

    def _is_self_attr(self, node: ast.expr) -> bool:
        return isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self"

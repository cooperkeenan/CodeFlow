import ast

from models.module_record import ModuleRecord
from models.project_index import ProjectIndex


class RoutePrefixIndex:
    def __init__(self, index: ProjectIndex) -> None:
        self._prefixes: dict[str, str] = {}
        for module_fqn, module in index.modules.items():
            record = index.functions.get(f"{module_fqn}.<module>")
            if record is None:
                continue
            for node in ast.walk(record.body):
                self._collect(node, module)

    def prefix_for(self, router_fqn: str) -> str:
        return self._prefixes.get(router_fqn, "")

    def _collect(self, node: ast.AST, module: ModuleRecord) -> None:
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            return
        if node.func.attr != "include_router" or not node.args or not isinstance(node.args[0], ast.Name):
            return
        target = module.bindings.get(node.args[0].id)
        prefix = self._prefix_kwarg(node)
        if target is not None and prefix:
            self._prefixes[target] = prefix

    def _prefix_kwarg(self, node: ast.Call) -> str | None:
        for kw in node.keywords:
            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
        return None

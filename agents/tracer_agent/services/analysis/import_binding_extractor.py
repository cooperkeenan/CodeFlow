import ast

from services.analysis.path_fqn import package_of, resolve_absolute


class ImportBindingExtractor(ast.NodeVisitor):
    def __init__(self, relpath: str, module_fqn: str, project_modules: frozenset[str]) -> None:
        self._relpath = relpath
        self._module_fqn = module_fqn
        self._project_modules = project_modules
        self.bindings: dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".")[0]
            local = alias.asname or top
            target = alias.name if alias.asname else top
            self.bindings[local] = resolve_absolute(target, self._module_fqn, self._project_modules)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        source = self._resolve_source(node)
        for alias in node.names:
            if alias.name == "*":
                self.bindings[f"*{source}"] = source
                continue
            local = alias.asname or alias.name
            if source.startswith("ext:"):
                self.bindings[local] = source
            else:
                self.bindings[local] = f"{source}.{alias.name}"
        self.generic_visit(node)

    def _resolve_source(self, node: ast.ImportFrom) -> str:
        if node.level == 0:
            return resolve_absolute(node.module or "", self._module_fqn, self._project_modules)
        base = package_of(self._relpath)
        for _ in range(node.level - 1):
            base = base.rsplit(".", 1)[0] if "." in base else ""
        return f"{base}.{node.module}" if node.module else base

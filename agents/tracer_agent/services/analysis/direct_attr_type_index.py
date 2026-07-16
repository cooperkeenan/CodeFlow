import ast

from models.project_index import ProjectIndex
from services.analysis.module_local_names import local_names_of
from services.analysis.module_scope_resolver import ModuleScopeResolver

_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


class DirectAttrTypeIndex:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index
        self._attrs: dict[tuple[str, str], str] = {}
        self._build()

    def get(self, class_fqn: str, attr: str) -> str | None:
        return self._attrs.get((class_fqn, attr))

    def _build(self) -> None:
        for class_fqn in self._index.classes:
            init_record = self._index.functions.get(f"{class_fqn}.__init__")
            if init_record is None or not isinstance(init_record.body, _DEF_NODES):
                continue
            module = self._index.modules.get(init_record.module)
            if module is None:
                continue
            scope = ModuleScopeResolver(module.bindings, local_names_of(module), init_record.module, self._index)
            for node in ast.walk(init_record.body):
                self._record_assign(class_fqn, node, scope)

    def _record_assign(self, class_fqn: str, node: ast.AST, scope: ModuleScopeResolver) -> None:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            return
        target = node.targets[0]
        if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)):
            return
        if target.value.id != "self":
            return
        resolved = scope.resolve_node(node.value)
        if resolved is not None:
            self._attrs.setdefault((class_fqn, target.attr), resolved)

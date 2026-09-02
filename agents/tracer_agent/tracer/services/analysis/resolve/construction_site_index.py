import ast

from tracer.models.index_records import FunctionRecord, ProjectIndex
from tracer.services.analysis.resolve.module_scope_resolver import ModuleScopeResolver
from tracer.services.analysis.syntax.types import local_names_of


class ConstructionSiteIndex:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index
        self._sites: dict[tuple[str, str], set[str]] = {}
        self._build()

    def concrete_for(self, owning_class_fqn: str, param_name: str) -> str | None:
        seen = self._sites.get((owning_class_fqn, param_name))
        if seen is not None and len(seen) == 1:
            return next(iter(seen))
        return None

    def _build(self) -> None:
        for record in self._index.functions.values():
            module = self._index.modules.get(record.module)
            if module is None:
                continue
            scope = ModuleScopeResolver(module.bindings, local_names_of(module), record.module, self._index)
            for node in ast.walk(record.body):
                if isinstance(node, ast.Call):
                    self._record_call(node, record, scope)

    def _record_call(self, node: ast.Call, caller: FunctionRecord, scope: ModuleScopeResolver) -> None:
        target = scope.resolve_node(node)
        if target is None or target not in self._index.classes:
            return
        init_record = self._index.functions.get(f"{target}.__init__")
        if init_record is None:
            return
        param_names = [p.name for p in init_record.params]
        own_params = {p.name: p.annotation for p in caller.params}
        for i, arg in enumerate(node.args):
            if i < len(param_names):
                self._record_arg(target, param_names[i], arg, own_params, scope)
        for kw in node.keywords:
            if kw.arg is not None:
                self._record_arg(target, kw.arg, kw.value, own_params, scope)

    def _record_arg(
        self, target: str, param_name: str, arg: ast.expr, own_params: dict[str, str | None], scope: ModuleScopeResolver
    ) -> None:
        concrete: str | None = None
        if isinstance(arg, ast.Name) and arg.id in own_params and own_params[arg.id] is not None:
            concrete = own_params[arg.id]
        elif isinstance(arg, ast.Call):
            resolved = scope.resolve_node(arg)
            if resolved in self._index.classes:
                concrete = resolved
        if concrete is not None:
            self._sites.setdefault((target, param_name), set()).add(concrete)

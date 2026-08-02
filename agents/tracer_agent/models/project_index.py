from collections.abc import Mapping

from models.class_record import ClassRecord
from models.function_record import FunctionRecord
from models.module_record import ModuleRecord


class ProjectIndex:
    def __init__(
        self,
        modules: Mapping[str, ModuleRecord],
        classes: Mapping[str, ClassRecord],
        functions: Mapping[str, FunctionRecord],
        implementations_index: Mapping[str, tuple[str, ...]],
        *,
        sources: Mapping[str, str] = {},
        source_roots: frozenset[str] = frozenset(),
    ) -> None:
        self.modules = modules
        self.classes = classes
        self.functions = functions
        self._implementations = implementations_index
        self.sources = sources
        self.source_roots = source_roots

    def implementations(self, base_fqn: str) -> tuple[str, ...]:
        return self._implementations.get(base_fqn, ())

    def resolve(self, module_fqn: str, name: str) -> str | None:
        module = self.modules.get(module_fqn)
        if module is None:
            return None
        candidate = f"{module_fqn}.{name}"
        if candidate in module.classes or candidate in module.functions:
            return candidate
        bound = module.bindings.get(name)
        if bound is not None and not bound.startswith("ext:"):
            return bound
        return None

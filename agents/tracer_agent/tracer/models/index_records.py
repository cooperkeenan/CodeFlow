import ast
from collections.abc import Mapping
from dataclasses import dataclass, field

from shared.models.flow_graph import SourceRef


@dataclass(frozen=True)
class ModuleRecord:
    fqn: str
    bindings: Mapping[str, str]
    classes: tuple[str, ...]
    functions: tuple[str, ...]


@dataclass(frozen=True)
class ClassRecord:
    fqn: str
    bases: tuple[str, ...]
    methods: tuple[str, ...]
    attr_types: Mapping[str, str]
    span: SourceRef


@dataclass(frozen=True)
class ParamRecord:
    name: str
    annotation: str | None


@dataclass(frozen=True)
class FunctionRecord:
    fqn: str
    module: str
    cls: str | None
    name: str
    params: tuple[ParamRecord, ...]
    returns: str | None
    span: SourceRef
    is_async: bool
    decorators: tuple[str, ...]
    body: ast.AST = field(repr=False, compare=False)


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
        unparsed: tuple[str, ...] = (),
    ) -> None:
        self.unparsed = unparsed
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

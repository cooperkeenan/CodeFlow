import ast
from dataclasses import dataclass

from tracer.models.index_records import ClassRecord, ModuleRecord, ProjectIndex

_BUILTIN_BASE_NAMES = {
    "dict", "list", "set", "tuple", "frozenset", "str", "int", "float", "bool", "bytes",
    "Optional", "Any", "Sequence", "Mapping", "Iterable", "Iterator", "Union", "Callable",
}


def normalize_type(raw: str | None, index: ProjectIndex) -> str | None:
    if raw is None:
        return None
    if raw.startswith("ext:") or raw in index.classes:
        return raw
    base = raw.split("[")[0].split(".")[0].strip()
    if base in _BUILTIN_BASE_NAMES:
        return "ext:builtins"
    return raw


@dataclass(frozen=True)
class ClassAnalysis:
    record: ClassRecord
    is_abstract: bool
    is_protocol: bool
    method_names: frozenset[str]


def local_names_of(module: ModuleRecord) -> frozenset[str]:
    names = {fqn.rsplit(".", 1)[-1] for fqn in module.classes}
    names |= {fqn.rsplit(".", 1)[-1] for fqn in module.functions}
    return frozenset(names)


_BUILTIN_CTORS = {"dict", "list", "set", "tuple", "str", "int", "float", "bool", "frozenset", "bytes"}
_LITERAL_NODES = (
    ast.Dict, ast.List, ast.Set, ast.Tuple, ast.JoinedStr, ast.Constant,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
)


def literal_type_hint(node: ast.expr) -> str | None:
    if isinstance(node, _LITERAL_NODES):
        return "ext:builtins"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _BUILTIN_CTORS:
        return "ext:builtins"
    return None

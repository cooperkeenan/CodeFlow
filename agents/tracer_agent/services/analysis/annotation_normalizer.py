from models.project_index import ProjectIndex

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

import ast

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

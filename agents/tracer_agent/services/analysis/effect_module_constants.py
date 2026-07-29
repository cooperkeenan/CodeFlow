import ast
from collections.abc import Mapping


def module_string_constants(body: ast.AST) -> Mapping[str, str]:
    constants: dict[str, str] = {}
    for node in ast.walk(body):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        value = node.value
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            constants[target.id] = value.value
    return constants

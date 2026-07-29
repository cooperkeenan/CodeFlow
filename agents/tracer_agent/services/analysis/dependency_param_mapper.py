import ast

from models.project_index import ProjectIndex


class DependencyParamMapper:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index

    def param_for_attr(self, owner_class_fqn: str, attr: str) -> str | None:
        init_record = self._index.functions.get(f"{owner_class_fqn}.__init__")
        if init_record is None or not isinstance(init_record.body, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None
        for node in ast.walk(init_record.body):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)):
                continue
            if target.value.id == "self" and target.attr == attr and isinstance(node.value, ast.Name):
                return node.value.id
        return None

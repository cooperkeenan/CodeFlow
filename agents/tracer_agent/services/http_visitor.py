import ast

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "request"}


class HttpCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self._current_class: str | None = None
        self.calls: list[dict] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        prev = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev

    def visit_Call(self, node: ast.Call) -> None:
        if self._current_class and self._is_http_call(node):
            target = self._extract_target(node)
            if target:
                self.calls.append({"from": self._current_class, "to": target})
        self.generic_visit(node)

    def _is_http_call(self, node: ast.Call) -> bool:
        return isinstance(node.func, ast.Attribute) and node.func.attr in HTTP_METHODS

    def _extract_target(self, node: ast.Call) -> str | None:
        if node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
            if isinstance(arg, ast.Name):
                return arg.id
            if isinstance(arg, ast.JoinedStr):
                path = self._fstring_path(arg)
                if path:
                    return path
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return func.value.id
        return None

    def _fstring_path(self, node: ast.JoinedStr) -> str | None:
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                stripped = part.value.lstrip("/")
                if stripped:
                    return f"/{stripped}"
        return None

import ast

from tracer.models.index_records import FunctionRecord

_URL_FUNCS = frozenset({"path", "re_path", "url"})


def _is_urlpatterns(target: ast.expr) -> bool:
    return isinstance(target, ast.Name) and target.id == "urlpatterns"


def urlpatterns_lists(record: FunctionRecord) -> tuple[ast.List, ...]:
    found: list[ast.List] = []
    for stmt in ast.walk(record.body):
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.List):
            if len(stmt.targets) == 1 and _is_urlpatterns(stmt.targets[0]):
                found.append(stmt.value)
        elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.value, ast.List):
            if isinstance(stmt.op, ast.Add) and _is_urlpatterns(stmt.target):
                found.append(stmt.value)
    return tuple(sorted(found, key=lambda node: node.lineno))


def call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def include_target(call: ast.Call) -> str | None:
    if call_name(call) != "include" or not call.args:
        return None
    arg = call.args[0]
    return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None


def route_view(element: ast.expr) -> tuple[str, ast.expr] | None:
    if not isinstance(element, ast.Call) or call_name(element) not in _URL_FUNCS:
        return None
    if len(element.args) < 2:
        return None
    route = element.args[0]
    if isinstance(route, ast.Constant) and isinstance(route.value, str):
        return route.value, element.args[1]
    return None


def is_include(view: ast.expr) -> bool:
    return isinstance(view, ast.Call) and call_name(view) == "include"

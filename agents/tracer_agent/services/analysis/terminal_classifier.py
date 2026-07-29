import ast

from models.arm import Terminal

_TRIVIAL_WRAPPERS = (ast.With, ast.AsyncWith)


def classify_terminal(body: list[ast.stmt]) -> Terminal:
    if not body:
        return "falls_through"
    return _classify_stmt(body[-1])


def _classify_stmt(stmt: ast.stmt) -> Terminal:
    if isinstance(stmt, ast.Return):
        return "returns"
    if isinstance(stmt, ast.Raise):
        return "raises"
    if isinstance(stmt, ast.Continue):
        return "continues"
    if isinstance(stmt, _TRIVIAL_WRAPPERS):
        return classify_terminal(stmt.body)
    if isinstance(stmt, ast.If) and stmt.orelse:
        then_terminal = classify_terminal(stmt.body)
        else_terminal = classify_terminal(stmt.orelse)
        if then_terminal == else_terminal and then_terminal != "falls_through":
            return then_terminal
    return "falls_through"

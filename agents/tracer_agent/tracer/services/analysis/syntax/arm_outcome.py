import ast

from tracer.models.call_records import Outcome
from tracer.services.analysis.syntax.http_status_labels import status_call_label

_STATUS_KEYWORDS = frozenset({"status", "status_code"})
_FAILURE_FLOOR = 400


def classify_outcome(body: list[ast.stmt]) -> Outcome:
    if not body:
        return "continue"
    return _classify_stmt(body[-1])


def _classify_stmt(stmt: ast.stmt) -> Outcome:
    if isinstance(stmt, ast.Raise):
        return "failure"
    if isinstance(stmt, ast.Return):
        return "failure" if _is_error_return(stmt.value) else "success"
    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        return classify_outcome(stmt.body)
    if isinstance(stmt, ast.If) and stmt.orelse:
        return _combine(classify_outcome(stmt.body), classify_outcome(stmt.orelse))
    return "continue"


def _combine(first: Outcome, second: Outcome) -> Outcome:
    if "continue" in (first, second):
        return "continue"
    return "failure" if first == second == "failure" else "success"


def _is_error_return(value: ast.expr | None) -> bool:
    if not isinstance(value, ast.Call):
        return False
    label = status_call_label(value)
    if label is not None:
        return int(label) >= _FAILURE_FLOOR
    for keyword in value.keywords:
        if keyword.arg in _STATUS_KEYWORDS and isinstance(keyword.value, ast.Constant):
            code = keyword.value.value
            if isinstance(code, int) and code >= _FAILURE_FLOOR:
                return True
    return False

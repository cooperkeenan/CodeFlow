import ast

_STATUS_BY_CLASS = {
    "HttpResponseForbidden": 403,
    "HttpResponseNotFound": 404,
    "HttpResponseBadRequest": 400,
    "HttpResponseNotAllowed": 405,
    "HttpResponseGone": 410,
    "HttpResponseServerError": 500,
    "HttpResponseRedirect": 302,
    "HttpResponsePermanentRedirect": 301,
}
_STATUS_KWARG_CLASSES = frozenset({"HttpResponse", "Response", "JsonResponse"})


def _callee_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _status_kwarg(node: ast.Call) -> int | None:
    for keyword in node.keywords:
        if keyword.arg != "status":
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and isinstance(value.value, int):
            return value.value
    return None


def status_call_label(node: ast.Call) -> str | None:
    name = _callee_name(node)
    if name is None:
        return None
    if name in _STATUS_BY_CLASS:
        return str(_STATUS_BY_CLASS[name])
    if name in _STATUS_KWARG_CLASSES:
        code = _status_kwarg(node)
        if code is not None:
            return str(code)
    return None

import ast

from services.analysis.call_expr_split import split_call_target

_LOGGING_METHODS = frozenset({"debug", "info", "warning", "warn", "error", "exception", "critical"})
_LOGGING_RECEIVER_SUFFIXES = ("log", "logger")
_GETTEXT_NAMES = frozenset({"_", "gettext", "ugettext", "gettext_lazy", "ugettext_lazy"})
_BUILTIN_CONVERSIONS = frozenset({"int", "str", "len", "bool", "list", "dict", "set", "tuple", "float", "repr"})
_PRINT_NAME = "print"


def _final_segment(root: str | None, chain: list[str]) -> str | None:
    if chain:
        return chain[-1]
    return root


def _receiver_ends_in_log(root: str | None, chain: list[str]) -> bool:
    if not chain:
        return False
    receiver = chain[-2] if len(chain) >= 2 else root
    if receiver is None:
        return False
    return receiver.endswith(_LOGGING_RECEIVER_SUFFIXES)


def _is_logging_call(root: str | None, chain: list[str], final: str | None) -> bool:
    return final in _LOGGING_METHODS and _receiver_ends_in_log(root, chain)


def _is_builtin_conversion(fqn: str, final: str | None) -> bool:
    if final not in _BUILTIN_CONVERSIONS:
        return False
    return not fqn or fqn.startswith("ext:builtins")


def noise_rule(fqn: str, node: ast.Call) -> str | None:
    if fqn.startswith("ext:logging"):
        return "logging"
    root, chain = split_call_target(node.func)
    final = _final_segment(root, chain)
    if final is None:
        return None
    if _is_logging_call(root, chain, final):
        return "logging"
    if final == _PRINT_NAME and not chain:
        return "print"
    if final in _GETTEXT_NAMES:
        return "gettext"
    if _is_builtin_conversion(fqn, final):
        return "builtin"
    return None


def is_noise(fqn: str, node: ast.Call) -> bool:
    return noise_rule(fqn, node) is not None

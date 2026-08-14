import ast

from services.analysis.call_expr_split import truncated_source

_LABEL_MAX = 48


def clamp(text: str) -> str:
    if len(text) <= _LABEL_MAX:
        return text
    return text[: _LABEL_MAX - 1] + "…"


def unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparseable>"


def node_label(node: ast.AST) -> str:
    return clamp(unparse(node))


def call_label(node: ast.Call) -> str:
    return clamp(truncated_source(node))


def for_header(node: ast.For | ast.AsyncFor) -> str:
    prefix = "async for" if isinstance(node, ast.AsyncFor) else "for"
    return clamp(f"{prefix} {unparse(node.target)} in {unparse(node.iter)}")


def while_header(node: ast.While) -> str:
    return clamp(f"while {unparse(node.test)}")


def handler_label(handler: ast.ExceptHandler) -> str:
    if handler.type is None:
        return "except"
    return clamp(f"except {unparse(handler.type)}")

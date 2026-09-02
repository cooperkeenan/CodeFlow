import ast
from collections.abc import Iterator

_BLOCK_FIELDS = ("body", "orelse", "finalbody")


def walk_statements(root_body: list[ast.stmt]) -> Iterator[tuple[ast.stmt, list[ast.stmt], int]]:
    stack = [root_body]
    while stack:
        block = stack.pop()
        for index, stmt in enumerate(block):
            yield stmt, block, index
            for nested in _nested_blocks(stmt):
                stack.append(nested)


def _nested_blocks(node: ast.stmt) -> Iterator[list[ast.stmt]]:
    for field in _BLOCK_FIELDS:
        block = getattr(node, field, None)
        if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
            yield block
    if isinstance(node, ast.Try):
        for handler in node.handlers:
            yield handler.body
    if isinstance(node, ast.Match):
        for case in node.cases:
            yield case.body

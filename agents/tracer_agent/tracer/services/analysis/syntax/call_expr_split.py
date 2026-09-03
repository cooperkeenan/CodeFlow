import ast


def unwrap_await(node: ast.expr) -> ast.expr:
    return node.value if isinstance(node, ast.Await) else node


def split_chain_base(node: ast.expr) -> tuple[ast.expr, list[str]]:
    chain: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        chain.append(current.attr)
        current = current.value
    chain.reverse()
    return current, chain


def split_call_target(node: ast.expr) -> tuple[str | None, list[str]]:
    base, chain = split_chain_base(node)
    if isinstance(base, ast.Name):
        return base.id, chain
    return None, []


def truncated_source(node: ast.expr) -> str:
    try:
        source = ast.unparse(node)
    except Exception:
        source = "<unparseable>"
    return source[:120]


def call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None

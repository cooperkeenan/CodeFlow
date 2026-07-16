import ast

from services.analysis.call_expr_split import split_chain_base


class _SelectorReadsVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.reads: list[str] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:
        base, chain = split_chain_base(node)
        if isinstance(base, ast.Name):
            dotted = ".".join([base.id, *chain])
            if dotted not in self.reads:
                self.reads.append(dotted)
            return
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in self.reads:
            self.reads.append(node.id)


def selector_reads(node: ast.expr) -> tuple[str, ...]:
    visitor = _SelectorReadsVisitor()
    visitor.visit(node)
    return tuple(visitor.reads)

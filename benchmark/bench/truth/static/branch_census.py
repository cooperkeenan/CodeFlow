import ast
from collections import Counter
from dataclasses import dataclass

from bench.truth.static.py_files import SourceTree


@dataclass(frozen=True)
class Census:
    """A bounded, deterministic denominator for decision reporting.

    This is not a quality measure. It is the count of places the program can
    branch, established independently of the tool under test, so a statement like
    "22 decisions surfaced from 3,140 branch sites" has a denominator that is a
    fact rather than a judgement. It survives even if the LLM judge turns out
    unreliable.
    """

    total: int
    by_construct: dict[str, int]
    unparsed: tuple[str, ...]


class BranchCensus:
    """Counts AST-level branch sites.

    Ternaries (`a if b else c`) are excluded: they express value selection rather
    than a choice between courses of action, and including them would swamp the
    count with formatting and defaulting noise. Comprehension filters are excluded
    for the same reason. The exclusions are recorded here so the denominator's
    definition travels with the number.
    """

    COUNTED = ("if", "match_case", "except_handler", "boolean_op")

    def count(self, tree: SourceTree) -> Census:
        totals: Counter[str] = Counter()
        unparsed: list[str] = []

        for relative, text in tree.sources.items():
            try:
                parsed = ast.parse(text)
            except SyntaxError:
                unparsed.append(relative)
                continue
            for node in ast.walk(parsed):
                if isinstance(node, ast.If):
                    totals["if"] += 1
                elif isinstance(node, ast.match_case):
                    totals["match_case"] += 1
                elif isinstance(node, ast.ExceptHandler):
                    totals["except_handler"] += 1
                elif isinstance(node, ast.BoolOp):
                    totals["boolean_op"] += 1

        counted = {key: totals.get(key, 0) for key in self.COUNTED}
        return Census(
            total=sum(counted[key] for key in ("if", "match_case", "except_handler")),
            by_construct=counted,
            unparsed=tuple(sorted(unparsed)),
        )

import ast

from services.analysis.call_fqn_lookup import CallFqnLookup
from services.analysis.decision_step_builder import DecisionStepBuilder
from services.analysis.leaf_step_builder import LeafStepBuilder
from services.analysis.step_id_allocator import StepIdAllocator
from services.analysis.step_labels import for_header, while_header

_MAX_STEPS = 40
_MAX_DEPTH = 4


def _outermost_calls(node: ast.AST) -> list[ast.Call]:
    found: list[ast.Call] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Call):
            found.append(child)
        else:
            found.extend(_outermost_calls(child))
    return found


class FunctionStepVisitor:
    def __init__(self, owner_fqn: str, lookup: CallFqnLookup) -> None:
        self._budget = _MAX_STEPS
        self._dropped = 0
        self._marker: dict | None = None
        self._ids = StepIdAllocator()
        self._leaves = LeafStepBuilder(owner_fqn, lookup, self._ids)
        self._decisions = DecisionStepBuilder(self._ids, self._walk_body)

    def build(self, body: list[ast.stmt]) -> list[dict]:
        steps = self._walk_body(body, 0)
        if self._marker is not None:
            text = f"+{self._dropped} more steps"
            self._marker["label"] = text
            self._marker["raw"] = text
        return steps

    def _walk_body(self, stmts: list[ast.stmt], depth: int) -> list[dict]:
        if depth > _MAX_DEPTH:
            if not stmts:
                return []
            text = f"+{len(stmts)} more steps"
            return [{"kind": "more", "id": self._ids.next(), "raw": text, "label": text}]
        out: list[dict] = []
        for stmt in stmts:
            self._dispatch(stmt, depth, out)
        return out

    def _dispatch(self, stmt: ast.stmt, depth: int, out: list[dict]) -> None:
        if isinstance(stmt, ast.If):
            self._append(out, self._decisions.if_step(stmt, depth))
        elif isinstance(stmt, ast.Match):
            self._append(out, self._decisions.match_step(stmt, depth))
        elif isinstance(stmt, ast.Try):
            self._append(out, self._decisions.try_step(stmt, depth))
        elif isinstance(stmt, (ast.For, ast.AsyncFor)):
            self._append(out, self._decisions.loop_step(stmt, depth, for_header(stmt)))
        elif isinstance(stmt, ast.While):
            self._append(out, self._decisions.loop_step(stmt, depth, while_header(stmt)))
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            self._dispatch_with(stmt, depth, out)
        elif isinstance(stmt, ast.Return):
            self._append(out, self._leaves.return_step(stmt))
        elif isinstance(stmt, ast.Raise):
            self._append(out, self._leaves.raise_step(stmt))
        else:
            for call in _outermost_calls(stmt):
                step = self._leaves.call_step(call)
                if step is not None:
                    self._append(out, step)

    def _dispatch_with(self, stmt: ast.With | ast.AsyncWith, depth: int, out: list[dict]) -> None:
        for item in stmt.items:
            for call in _outermost_calls(item.context_expr):
                step = self._leaves.call_step(call)
                if step is not None:
                    self._append(out, step)
        out.extend(self._walk_body(stmt.body, depth))

    def _append(self, out: list[dict], step: dict) -> None:
        if self._budget <= 0:
            self._dropped += 1
            if self._marker is None:
                self._marker = {"kind": "more", "id": self._ids.next(), "raw": "", "label": ""}
                out.append(self._marker)
            return
        out.append(step)
        self._budget -= 1

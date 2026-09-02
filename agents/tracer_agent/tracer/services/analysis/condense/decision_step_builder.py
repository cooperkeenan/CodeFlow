import ast
from collections.abc import Callable

from tracer.services.analysis.condense.step_id_allocator import StepIdAllocator
from tracer.services.analysis.syntax.step_label_normalizer import normalize_label
from tracer.services.analysis.syntax.step_labels import handler_label, node_label

WalkBody = Callable[[list[ast.stmt], int], list[dict]]


class DecisionStepBuilder:
    def __init__(self, ids: StepIdAllocator, walk_body: WalkBody) -> None:
        self._ids = ids
        self._walk_body = walk_body

    def if_step(self, stmt: ast.If, depth: int) -> dict:
        step_id = self._ids.next()
        raw = node_label(stmt.test)
        arms = [{"label": "Yes", "steps": self._walk_body(stmt.body, depth + 1)}]
        arms.append({"label": "No", "steps": self._walk_body(stmt.orelse, depth + 1) if stmt.orelse else []})
        return self._decision(step_id, raw, stmt.lineno, arms)

    def match_step(self, stmt: ast.Match, depth: int) -> dict:
        step_id = self._ids.next()
        raw = node_label(stmt.subject)
        arms = [
            {"label": node_label(case.pattern), "steps": self._walk_body(case.body, depth + 1)}
            for case in stmt.cases
        ]
        return self._decision(step_id, raw, stmt.lineno, arms)

    def try_step(self, stmt: ast.Try, depth: int) -> dict:
        step_id = self._ids.next()
        arms = [{"label": "ok", "steps": self._walk_body(stmt.body, depth + 1)}]
        for handler in stmt.handlers:
            arms.append({"label": handler_label(handler), "steps": self._walk_body(handler.body, depth + 1)})
        if stmt.orelse:
            arms.append({"label": "else", "steps": self._walk_body(stmt.orelse, depth + 1)})
        if stmt.finalbody:
            arms.append({"label": "finally", "steps": self._walk_body(stmt.finalbody, depth + 1)})
        return self._decision(step_id, "try", stmt.lineno, arms)

    def loop_step(self, stmt: ast.For | ast.AsyncFor | ast.While, depth: int, raw: str) -> dict:
        step_id = self._ids.next()
        body = self._walk_body(stmt.body, depth + 1)
        return {
            "kind": "loop",
            "id": step_id,
            "raw": raw,
            "label": normalize_label("loop", raw),
            "line": stmt.lineno,
            "body": body,
        }

    def _decision(self, step_id: str, raw: str, line: int, arms: list[dict]) -> dict:
        return {
            "kind": "decision",
            "id": step_id,
            "raw": raw,
            "label": normalize_label("decision", raw),
            "line": line,
            "arms": arms,
        }

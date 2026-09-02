import ast

from tracer.services.analysis.condense.step_id_allocator import StepIdAllocator
from tracer.services.analysis.resolve.indexes import CallFqnLookup
from tracer.services.analysis.syntax.call_expr_split import truncated_source
from tracer.services.analysis.syntax.http_status_labels import status_call_label
from tracer.services.analysis.syntax.noise_pruning import noise_rule
from tracer.services.analysis.syntax.step_label_normalizer import normalize_label
from tracer.services.analysis.syntax.step_labels import call_label, node_label


class LeafStepBuilder:
    def __init__(self, owner_fqn: str, lookup: CallFqnLookup, ids: StepIdAllocator) -> None:
        self._owner_fqn = owner_fqn
        self._lookup = lookup
        self._ids = ids

    def return_step(self, stmt: ast.Return) -> dict:
        raw = node_label(stmt)
        label = self._status_label(stmt.value) or normalize_label("return", raw)
        return {"kind": "return", "id": self._ids.next(), "raw": raw, "label": label, "line": stmt.lineno}

    def raise_step(self, stmt: ast.Raise) -> dict:
        raw = node_label(stmt)
        return {
            "kind": "raise",
            "id": self._ids.next(),
            "raw": raw,
            "label": normalize_label("raise", raw),
            "line": stmt.lineno,
        }

    def call_step(self, node: ast.Call) -> dict | None:
        raw_for_lookup = truncated_source(node)
        fqn = self._lookup.fqn_for(self._owner_fqn, node.lineno, raw_for_lookup)
        if noise_rule(fqn, node) is not None:
            return None
        external = fqn.startswith("ext:")
        raw = call_label(node)
        return {
            "kind": "effect" if external else "call",
            "id": self._ids.next(),
            "raw": raw,
            "label": normalize_label("call", raw),
            "line": node.lineno,
            "fqn": fqn,
            "external": external,
        }

    def _status_label(self, value: ast.expr | None) -> str | None:
        if not isinstance(value, ast.Call):
            return None
        code = status_call_label(value)
        return f"return {code}" if code is not None else None

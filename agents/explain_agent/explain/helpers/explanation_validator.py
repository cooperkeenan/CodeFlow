from typing import TypeVar

from explain.models.explain_model import (
    ExplainRequest,
    HelperExplanation,
    MethodExplanation,
    NodeExplanation,
)
from explain.models.symbol_slice import SymbolSlice

_MAX_SUMMARY_WORDS = 12
_MAX_PRIMARY_WORDS = 40

_Explanation = TypeVar("_Explanation", MethodExplanation, HelperExplanation)


class ExplanationValidator:
    def validate(
        self, raw: dict, request: ExplainRequest, fallback: NodeExplanation
    ) -> NodeExplanation:
        raw_methods = self._as_dict(raw.get("methods"))
        raw_helpers = self._as_dict(raw.get("helpers"))
        fallback_methods = {m.fqn: m.summary for m in fallback.methods}
        fallback_helpers = {h.fqn: h.summary for h in fallback.helpers}
        methods = self._build(raw_methods, request.symbols, fallback_methods, MethodExplanation)
        helpers = self._build(raw_helpers, request.helpers, fallback_helpers, HelperExplanation)
        primary_summary = (
            self._clamp(raw.get("primary_summary"), _MAX_PRIMARY_WORDS) or fallback.primary_summary
        )
        return NodeExplanation(
            node_id=fallback.node_id,
            focus_fqn=fallback.focus_fqn,
            service=fallback.service,
            primary_kind=fallback.primary_kind,
            primary_name=fallback.primary_name,
            primary_summary=primary_summary,
            methods=methods,
            helpers=helpers,
            generated=True,
        )

    def _as_dict(self, value: object) -> dict:
        return value if isinstance(value, dict) else {}

    def _build(
        self,
        raw: dict,
        symbols: list[SymbolSlice],
        fallback: dict[str, str],
        model_cls: type[_Explanation],
    ) -> list[_Explanation]:
        entries: list[_Explanation] = []
        for symbol in symbols:
            summary = self._clamp(raw.get(symbol.fqn)) or self._clamp(fallback.get(symbol.fqn, ""))
            entries.append(model_cls(name=symbol.name, fqn=symbol.fqn, summary=summary))
        return entries

    def _clamp(self, value: object, limit: int = _MAX_SUMMARY_WORDS) -> str:
        if not isinstance(value, str):
            return ""
        words = value.strip().split()
        return " ".join(words[:limit])

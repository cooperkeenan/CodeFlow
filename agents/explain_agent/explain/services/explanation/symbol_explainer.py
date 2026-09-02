from typing import Protocol

from explain.models.explain_model import ExplainRequest, NodeExplanation


class SymbolExplainer(Protocol):
    def explain(self, request: ExplainRequest) -> NodeExplanation: ...

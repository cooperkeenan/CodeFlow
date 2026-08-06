from typing import Protocol

from models.explain_model import ExplainRequest, NodeExplanation


class SymbolExplainer(Protocol):
    def explain(self, request: ExplainRequest) -> NodeExplanation: ...

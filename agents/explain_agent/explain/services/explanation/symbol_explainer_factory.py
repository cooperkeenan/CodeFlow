import anthropic
from explain.helpers.explanation_validator import ExplanationValidator
from explain.helpers.step_label_validator import StepLabelValidator
from explain.services.explanation.heuristic_symbol_explainer import (
    HeuristicSymbolExplainer,
)
from explain.services.explanation.llm_symbol_explainer import LlmSymbolExplainer
from explain.services.explanation.symbol_explainer import SymbolExplainer


def build_symbol_explainer(api_key: str) -> SymbolExplainer:
    fallback = HeuristicSymbolExplainer()
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return LlmSymbolExplainer(client, fallback, ExplanationValidator(), StepLabelValidator())

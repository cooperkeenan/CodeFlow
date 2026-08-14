import anthropic
from helpers.explanation_validator import ExplanationValidator
from helpers.step_label_validator import StepLabelValidator
from services.explanation.heuristic_symbol_explainer import HeuristicSymbolExplainer
from services.explanation.llm_symbol_explainer import LlmSymbolExplainer
from services.explanation.symbol_explainer import SymbolExplainer


def build_symbol_explainer(api_key: str) -> SymbolExplainer:
    fallback = HeuristicSymbolExplainer()
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return LlmSymbolExplainer(client, fallback, ExplanationValidator(), StepLabelValidator())

from explain.core.config import Settings, get_settings
from explain.services.explanation.symbol_explainer import SymbolExplainer
from explain.services.explanation.symbol_explainer_factory import build_symbol_explainer
from fastapi import Depends


def get_symbol_explainer(
    settings: Settings = Depends(get_settings),
) -> SymbolExplainer:
    return build_symbol_explainer(settings.ANTHROPIC_API_KEY)

from core.config import Settings, get_settings
from fastapi import Depends

from services.explanation.symbol_explainer import SymbolExplainer
from services.explanation.symbol_explainer_factory import build_symbol_explainer


def get_symbol_explainer(
    settings: Settings = Depends(get_settings),
) -> SymbolExplainer:
    return build_symbol_explainer(settings.ANTHROPIC_API_KEY)

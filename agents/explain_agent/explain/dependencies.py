from explain.core.config import Settings, get_settings
from explain.services.contract.contract_writer import ContractWriter
from explain.services.contract.contract_writer_factory import build_contract_writer
from explain.services.explanation.symbol_explainer import SymbolExplainer
from explain.services.explanation.symbol_explainer_factory import build_symbol_explainer
from fastapi import Depends


def get_symbol_explainer(
    settings: Settings = Depends(get_settings),
) -> SymbolExplainer:
    return build_symbol_explainer(settings.ANTHROPIC_API_KEY)


def get_contract_writer(
    settings: Settings = Depends(get_settings),
) -> ContractWriter:
    return build_contract_writer(settings.ANTHROPIC_API_KEY)

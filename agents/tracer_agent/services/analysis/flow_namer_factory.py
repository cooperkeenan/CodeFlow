from pathlib import Path

import anthropic
from services.analysis.anthropic_key import anthropic_api_key
from services.analysis.flow_naming import FlowNaming
from services.analysis.flow_namer import FlowNamer
from services.analysis.heuristic_flow_namer import HeuristicFlowNamer
from services.analysis.name_cache import NameCache
from services.analysis.name_validator import NameValidator


def build_flow_namer(cache_path: Path) -> FlowNaming:
    fallback = HeuristicFlowNamer()
    api_key = anthropic_api_key()
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return FlowNamer(client, NameCache(cache_path), NameValidator())

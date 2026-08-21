from pathlib import Path

import anthropic
from services.analysis.anthropic_key import anthropic_api_key
from services.analysis.flow_reviewer import FlowReviewer
from services.analysis.flow_reviewing import FlowReviewing
from services.analysis.heuristic_flow_reviewer import HeuristicFlowReviewer
from services.analysis.name_validator import NameValidator
from services.analysis.review_cache import ReviewCache


def build_flow_reviewer(cache_path: Path) -> FlowReviewing:
    fallback = HeuristicFlowReviewer()
    api_key = anthropic_api_key()
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return FlowReviewer(client, ReviewCache(cache_path), NameValidator())

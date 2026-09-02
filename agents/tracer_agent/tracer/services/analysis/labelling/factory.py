from pathlib import Path

import anthropic
from tracer.services.analysis.contracts import FlowNaming, FlowReviewing
from tracer.services.analysis.labelling.flow_namer import FlowNamer
from tracer.services.analysis.labelling.flow_reviewer import FlowReviewer
from tracer.services.analysis.labelling.heuristics import (
    HeuristicFlowNamer,
    HeuristicFlowReviewer,
)
from tracer.services.analysis.labelling.name_cache import NameCache
from tracer.services.analysis.labelling.name_validator import NameValidator
from tracer.services.analysis.labelling.review_cache import ReviewCache


def build_flow_namer(api_key: str | None, cache_path: Path) -> FlowNaming:
    fallback = HeuristicFlowNamer()
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return FlowNamer(client, NameCache(cache_path), NameValidator())


def build_flow_reviewer(api_key: str | None, cache_path: Path) -> FlowReviewing:
    fallback = HeuristicFlowReviewer()
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return FlowReviewer(client, ReviewCache(cache_path), NameValidator())

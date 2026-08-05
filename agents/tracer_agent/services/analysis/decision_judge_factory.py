import os
from pathlib import Path

import anthropic
from services.analysis.decision_judge import DecisionJudge
from services.analysis.heuristic_decision_judge import HeuristicDecisionJudge
from services.analysis.llm_decision_judge import LlmDecisionJudge
from services.analysis.site_classifier import SiteClassifier
from services.analysis.verdict_cache import VerdictCache


def build_decision_judge(cache_path: Path) -> DecisionJudge:
    fallback = HeuristicDecisionJudge(SiteClassifier())
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return LlmDecisionJudge(client, fallback, VerdictCache(cache_path))

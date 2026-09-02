from pathlib import Path

import anthropic
from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.config import SignificanceConfig
from tracer.services.analysis.contracts import DecisionJudge
from tracer.services.analysis.forks.arm_classifier import ArmClassifier
from tracer.services.analysis.labelling.verdict_cache import VerdictCache
from tracer.services.analysis.resolve.call_graph import CallGraphBuilder
from tracer.services.analysis.resolve.indexes import ComponentIndex
from tracer.services.analysis.significance.decision_candidate_builder import (
    DecisionCandidateBuilder,
)
from tracer.services.analysis.significance.heuristic_decision_judge import (
    HeuristicDecisionJudge,
)
from tracer.services.analysis.significance.llm_decision_judge import LlmDecisionJudge
from tracer.services.analysis.significance.route_reach_index import (
    RouteReachIndexBuilder,
)
from tracer.services.analysis.significance.scc_index_builder import SccIndexBuilder
from tracer.services.analysis.significance.significance_filter import SignificanceFilter
from tracer.services.analysis.significance.site_classifier import SiteClassifier
from tracer.services.analysis.significance.utility_damper import UtilityDamper


def build_significance_filter(
    index: ProjectIndex,
    config: SignificanceConfig | None = None,
    judge: DecisionJudge | None = None,
) -> SignificanceFilter:
    resolved_config = config or SignificanceConfig()
    components = ComponentIndex(index)
    arm_classifier = ArmClassifier(resolved_config)
    resolved_judge = judge or HeuristicDecisionJudge(SiteClassifier())
    return SignificanceFilter(
        index=index,
        components=components,
        config=resolved_config,
        damper=UtilityDamper(components, resolved_config),
        graph_builder=CallGraphBuilder(components),
        scc_builder=SccIndexBuilder(),
        candidate_builder=DecisionCandidateBuilder(components, arm_classifier, index.sources),
        judge=resolved_judge,
        route_reach_builder=RouteReachIndexBuilder(),
    )


def build_decision_judge(api_key: str | None, cache_path: Path) -> DecisionJudge:
    fallback = HeuristicDecisionJudge(SiteClassifier())
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return LlmDecisionJudge(client, fallback, VerdictCache(cache_path))

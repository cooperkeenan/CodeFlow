from models.project_index import ProjectIndex
from services.analysis.arm_classifier import ArmClassifier
from services.analysis.call_graph import CallGraphBuilder
from services.analysis.component_index import ComponentIndex
from services.analysis.decision_candidate_builder import DecisionCandidateBuilder
from services.analysis.decision_judge import DecisionJudge
from services.analysis.heuristic_decision_judge import HeuristicDecisionJudge
from services.analysis.route_reach_index import RouteReachIndexBuilder
from services.analysis.scc_index_builder import SccIndexBuilder
from services.analysis.significance_config import SignificanceConfig
from services.analysis.significance_filter import SignificanceFilter
from services.analysis.site_classifier import SiteClassifier
from services.analysis.utility_damper import UtilityDamper


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

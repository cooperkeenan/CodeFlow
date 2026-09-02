from tracer.models.call_records import CallSite
from tracer.models.index_records import ProjectIndex
from tracer.models.sites import DispatchSite
from tracer.models.verdicts import (
    DecisionCandidate,
    DecisionVerdict,
    SignificanceResult,
    SiteVerdict,
)
from tracer.services.analysis.config import SignificanceConfig
from tracer.services.analysis.contracts import DecisionJudge
from tracer.services.analysis.resolve.call_graph import CallGraphBuilder
from tracer.services.analysis.resolve.indexes import ComponentIndex
from tracer.services.analysis.significance.decision_candidate_builder import (
    DecisionCandidateBuilder,
)
from tracer.services.analysis.significance.reach_computer import ReachComputer
from tracer.services.analysis.significance.route_reach_index import (
    RouteReachIndexBuilder,
)
from tracer.services.analysis.significance.scc_index_builder import SccIndexBuilder
from tracer.services.analysis.significance.site_scorer import SiteScorer
from tracer.services.analysis.significance.utility_damper import UtilityDamper


class SignificanceFilter:
    def __init__(
        self,
        index: ProjectIndex,
        components: ComponentIndex,
        config: SignificanceConfig,
        damper: UtilityDamper,
        graph_builder: CallGraphBuilder,
        scc_builder: SccIndexBuilder,
        candidate_builder: DecisionCandidateBuilder,
        judge: DecisionJudge,
        route_reach_builder: RouteReachIndexBuilder,
    ) -> None:
        self._index = index
        self._components = components
        self._config = config
        self._damper = damper
        self._graph_builder = graph_builder
        self._scc_builder = scc_builder
        self._candidate_builder = candidate_builder
        self._judge = judge
        self._route_reach_builder = route_reach_builder

    def run(
        self, callsites: tuple[CallSite, ...], sites: tuple[DispatchSite, ...]
    ) -> SignificanceResult:
        utilities = self._damper.compute(callsites)
        graph = self._graph_builder.build(callsites)
        reach = ReachComputer(graph, self._scc_builder.build(graph), self._components, utilities)
        scorer = SiteScorer(self._config, self._index, self._route_reach_builder.build(sites, graph))
        candidates = tuple(
            self._candidate_builder.build(site, reach, scorer) for site in sites
        )
        judge_verdicts = self._judge.judge(candidates)
        verdicts: dict[str, SiteVerdict] = {}
        ranking: list[tuple[float, float, str, int, str]] = []
        for site, candidate in zip(sites, candidates):
            verdict = self._site_verdict(site, candidate, judge_verdicts[site.id])
            verdicts[site.id] = verdict
            if verdict.verdict == "decision":
                ranking.append((verdict.importance, verdict.score, site.owner, site.span.line, site.id))
        ranked = tuple(
            item[4] for item in sorted(ranking, key=lambda i: (-i[0], -i[1], i[2], i[3]))
        )
        return SignificanceResult(utilities=utilities, verdicts=verdicts, ranked_decisions=ranked)

    def _site_verdict(
        self, site: DispatchSite, candidate: DecisionCandidate, decision_verdict: DecisionVerdict
    ) -> SiteVerdict:
        score = candidate.heuristic_score if decision_verdict.verdict == "decision" else 0.0
        return SiteVerdict(
            site_id=site.id,
            verdict=decision_verdict.verdict,
            score=score,
            arm_reach_sizes=candidate.arm_reach_sizes,
            arm_classes=candidate.arm_classes,
            question=decision_verdict.question,
            arm_labels=decision_verdict.arm_labels,
            importance=decision_verdict.importance,
        )

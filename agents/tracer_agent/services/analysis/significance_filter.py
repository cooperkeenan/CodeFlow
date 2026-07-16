from models.call_site import CallSite
from models.dispatch_site import DispatchSite
from models.project_index import ProjectIndex
from models.significance_result import SignificanceResult
from models.site_verdict import ArmClass, SiteVerdict
from services.analysis.arm_classifier import ArmClassifier
from services.analysis.call_graph import CallGraphBuilder
from services.analysis.component_index import ComponentIndex
from services.analysis.reach_computer import ReachComputer
from services.analysis.route_reach_index import RouteReachIndexBuilder
from services.analysis.scc_index_builder import SccIndexBuilder
from services.analysis.significance_config import SignificanceConfig
from services.analysis.site_classifier import SiteClassifier
from services.analysis.site_scorer import SiteScorer
from services.analysis.utility_damper import UtilityDamper


class SignificanceFilter:
    def __init__(
        self,
        index: ProjectIndex,
        components: ComponentIndex,
        config: SignificanceConfig,
        damper: UtilityDamper,
        graph_builder: CallGraphBuilder,
        scc_builder: SccIndexBuilder,
        arm_classifier: ArmClassifier,
        site_classifier: SiteClassifier,
        route_reach_builder: RouteReachIndexBuilder,
    ) -> None:
        self._index = index
        self._components = components
        self._config = config
        self._damper = damper
        self._graph_builder = graph_builder
        self._scc_builder = scc_builder
        self._arm_classifier = arm_classifier
        self._site_classifier = site_classifier
        self._route_reach_builder = route_reach_builder

    def run(
        self, callsites: tuple[CallSite, ...], sites: tuple[DispatchSite, ...]
    ) -> SignificanceResult:
        utilities = self._damper.compute(callsites)
        graph = self._graph_builder.build(callsites)
        reach = ReachComputer(graph, self._scc_builder.build(graph), self._components, utilities)
        scorer = SiteScorer(self._config, self._index, self._route_reach_builder.build(sites, graph))
        verdicts: dict[str, SiteVerdict] = {}
        ranking: list[tuple[float, str, int, str]] = []
        for site in sites:
            verdict = self._verdict_for(site, reach, scorer)
            verdicts[site.id] = verdict
            if verdict.verdict == "decision":
                ranking.append((verdict.score, site.owner, site.span.line, site.id))
        ranked = tuple(item[3] for item in sorted(ranking, key=lambda i: (-i[0], i[1], i[2])))
        return SignificanceResult(utilities=utilities, verdicts=verdicts, ranked_decisions=ranked)

    def _verdict_for(
        self, site: DispatchSite, reach: ReachComputer, scorer: SiteScorer
    ) -> SiteVerdict:
        owner_component = self._components.component_of(site.owner)
        reaches = tuple(reach.arm_reach(arm, owner_component) for arm in site.arms)
        classes: tuple[ArmClass, ...] = tuple(
            self._arm_classifier.classify(arm, r) for arm, r in zip(site.arms, reaches)
        )
        verdict = self._site_classifier.classify(site, classes, reaches)
        live_union = frozenset().union(
            *(reaches[i] for i, cls in enumerate(classes) if cls == "live")
        )
        score = scorer.score(site, live_union) if verdict == "decision" else 0.0
        return SiteVerdict(
            site_id=site.id,
            verdict=verdict,
            score=score,
            arm_reach_sizes=tuple(len(r) for r in reaches),
            arm_classes=classes,
        )

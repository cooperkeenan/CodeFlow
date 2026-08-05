from collections.abc import Mapping

from models.pillar_scores import PillarScores
from models.review_finding import ReviewFinding
from models.significance_result import SignificanceResult
from shared.models.flow_graph import FlowGraph

from services.analysis.call_resolver import CallResolver
from services.analysis.decision_judge import DecisionJudge
from services.analysis.dispatch_extractor_factory import build_dispatch_extractor
from services.analysis.effect_detector import EffectDetector
from services.analysis.entry_finder import EntryFinder
from services.analysis.flow_condenser_factory import build_flow_condenser
from services.analysis.flow_naming import FlowNaming
from services.analysis.flow_reviewing import FlowReviewing
from services.analysis.flow_stitcher import FlowStitcher
from services.analysis.component_index import ComponentIndex
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.pillar_ranker import PillarRanker
from services.analysis.visibility_budgeter import VisibilityBudgeter
from services.analysis.project_indexer import ProjectIndexer
from services.analysis.route_handler_locator import RouteHandlerLocator
from services.analysis.service_root_resolver import ServiceRootResolver
from services.analysis.significance_config import SignificanceConfig
from services.analysis.significance_filter_factory import build_significance_filter


class FlowPipeline:
    def __init__(
        self,
        indexer: ProjectIndexer,
        effect_detector: EffectDetector,
        stitcher: FlowStitcher,
        budgeter: VisibilityBudgeter,
        significance_config: SignificanceConfig | None = None,
        service_hints: frozenset[str] | None = None,
        judge: DecisionJudge | None = None,
        namer: FlowNaming | None = None,
        reviewer: FlowReviewing | None = None,
    ) -> None:
        self._indexer = indexer
        self._effects = effect_detector
        self._stitcher = stitcher
        self._budgeter = budgeter
        self._config = significance_config or SignificanceConfig()
        self._hints = service_hints
        self._judge = judge
        self._namer = namer
        self._reviewer = reviewer
        self._last_significance: SignificanceResult | None = None
        self._last_pillars: PillarScores | None = None
        self._last_pre_review: FlowGraph | None = None
        self._last_review: list[ReviewFinding] | None = None

    def last_significance(self) -> SignificanceResult | None:
        return self._last_significance

    def last_pillars(self) -> PillarScores | None:
        return self._last_pillars

    def last_pre_review(self) -> FlowGraph | None:
        return self._last_pre_review

    def last_review(self) -> list[ReviewFinding] | None:
        return self._last_review

    def run(self, repo: str, files: Mapping[str, str]) -> FlowGraph:
        index = self._indexer.index(files)
        callsites = CallResolver(index).resolve_project()
        dispatch = build_dispatch_extractor(index).extract(callsites)
        effects = self._effects.detect(index, callsites)
        significance = build_significance_filter(index, self._config, judge=self._judge).run(
            callsites, dispatch
        )
        self._last_significance = significance
        graph = build_flow_condenser(self._hints, index.source_roots).condense(
            repo, index, callsites, dispatch, effects, significance
        )
        entries = EntryFinder(
            index,
            RouteHandlerLocator(index),
            ServiceRootResolver(self._hints, index.source_roots),
            LabelSynthesizer(),
        ).find(dispatch)
        stitched = self._stitcher.stitch(graph, effects, entries)
        components = ComponentIndex(index)
        pillars = PillarRanker(components, self._config).rank(callsites)
        self._last_pillars = pillars
        budgeted = self._budgeter.budget(stitched, pillars, components)
        named = budgeted if self._namer is None else self._namer.name(budgeted)
        self._last_pre_review = named
        if self._reviewer is None:
            return named
        reviewed = self._reviewer.review(named)
        self._last_review = [
            ReviewFinding(node_id=finding["node_id"], issue=finding["issue"])
            for finding in reviewed.meta.get("review_findings", [])
        ]
        return reviewed

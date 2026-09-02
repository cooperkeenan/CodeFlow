import logging
from collections.abc import Mapping

from tracer.models.naming import ReviewFinding
from tracer.models.pillar_scores import PillarScores
from tracer.models.verdicts import SignificanceResult
from tracer.services.analysis.budget.visibility_budgeter import VisibilityBudgeter
from tracer.services.analysis.condense.factory import (
    build_flow_condenser,
)
from tracer.services.analysis.config import SignificanceConfig
from tracer.services.analysis.contracts import DecisionJudge, FlowNaming, FlowReviewing
from tracer.services.analysis.effects.effect_detector import EffectDetector
from tracer.services.analysis.forks.factory import (
    build_dispatch_extractor,
)
from tracer.services.analysis.indexing.project_indexer import ProjectIndexer
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.ranking.pillar_ranker import PillarRanker
from tracer.services.analysis.resolve.call_resolver import CallResolver
from tracer.services.analysis.resolve.indexes import ComponentIndex
from tracer.services.analysis.routes.entry_finder import EntryFinder
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer
from tracer.services.analysis.routes.route_handler_locator import RouteHandlerLocator
from tracer.services.analysis.significance.factory import (
    build_significance_filter,
)
from tracer.services.analysis.stitch.flow_stitcher import FlowStitcher
from tracer.services.analysis.symbols.symbol_context_builder import SymbolContextBuilder
from tracer.services.analysis.symbols.symbol_source_reader import SymbolSourceReader

from shared.models.flow_graph import FlowGraph

logger = logging.getLogger(__name__)


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
        embed_symbol_sources: bool = False,
    ) -> None:
        self._embed_sources = embed_symbol_sources
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
        if index.unparsed:
            logger.warning(
                "%d file(s) could not be parsed and are missing from the graph: %s",
                len(index.unparsed),
                ", ".join(index.unparsed[:5]),
            )
        reader = SymbolSourceReader(index.sources) if self._embed_sources else None
        symbol_context = SymbolContextBuilder(
            index, callsites, ServiceRootResolver(self._hints, index.source_roots), reader
        )
        if self._reviewer is None:
            named.meta["symbol_context"] = symbol_context.build(named)
            return named
        reviewed = self._reviewer.review(named)
        self._last_review = [
            ReviewFinding(node_id=finding["node_id"], issue=finding["issue"])
            for finding in reviewed.meta.get("review_findings", [])
        ]
        reviewed.meta["symbol_context"] = symbol_context.build(reviewed)
        return reviewed

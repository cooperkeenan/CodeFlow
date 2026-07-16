from collections.abc import Mapping

from shared.models.flow_graph import FlowGraph

from services.analysis.call_resolver import CallResolver
from services.analysis.dispatch_extractor_factory import build_dispatch_extractor
from services.analysis.effect_detector import EffectDetector
from services.analysis.entry_finder import EntryFinder
from services.analysis.flow_condenser_factory import build_flow_condenser
from services.analysis.flow_stitcher import FlowStitcher
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.page_budgeter import PageBudgeter
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
        budgeter: PageBudgeter,
        significance_config: SignificanceConfig | None = None,
        service_hints: frozenset[str] | None = None,
    ) -> None:
        self._indexer = indexer
        self._effects = effect_detector
        self._stitcher = stitcher
        self._budgeter = budgeter
        self._config = significance_config or SignificanceConfig()
        self._hints = service_hints

    def run(self, repo: str, files: Mapping[str, str]) -> FlowGraph:
        index = self._indexer.index(files)
        callsites = CallResolver(index).resolve_project()
        dispatch = build_dispatch_extractor(index).extract(callsites)
        effects = self._effects.detect(index, callsites)
        significance = build_significance_filter(index, self._config).run(callsites, dispatch)
        graph = build_flow_condenser(self._hints).condense(
            repo, index, callsites, dispatch, effects, significance
        )
        entries = EntryFinder(
            index,
            RouteHandlerLocator(index),
            ServiceRootResolver(self._hints),
            LabelSynthesizer(),
        ).find(dispatch)
        stitched = self._stitcher.stitch(graph, effects, entries)
        return self._budgeter.budget(stitched, significance)

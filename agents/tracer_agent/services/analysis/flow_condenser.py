from models.call_site import CallSite
from models.dispatch_site import DispatchSite
from models.effect_site import EffectSite
from models.project_index import ProjectIndex
from models.significance_result import SignificanceResult
from shared.models.flow_graph import FlowGraph

from services.analysis.anchor_index import AnchorIndex
from services.analysis.anchor_resolver import AnchorResolver
from services.analysis.call_ancestry_resolver import CallAncestryResolver
from services.analysis.component_index import ComponentIndex
from services.analysis.container_assigner import ContainerAssigner
from services.analysis.container_repointer import ContainerRepointer
from services.analysis.decision_seeder import DecisionSeeder
from services.analysis.entry_finder import EntryFinder
from services.analysis.event_collector import EventCollector
from services.analysis.function_summarizer import FunctionSummarizer
from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.island_anchor import IslandAnchor
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.lane_builder import LaneBuilder
from services.analysis.parallel_detector import ParallelDetector
from services.analysis.route_handler_locator import RouteHandlerLocator
from services.analysis.service_root_resolver import ServiceRootResolver
from services.analysis.step_merger import StepMerger
from services.analysis.trivial_entry_folder import TrivialEntryFolder


class FlowCondenser:
    def __init__(self, roots: ServiceRootResolver, labels: LabelSynthesizer) -> None:
        self._roots = roots
        self._labels = labels

    def condense(
        self,
        repo: str,
        index: ProjectIndex,
        callsites: tuple[CallSite, ...],
        dispatch_sites: tuple[DispatchSite, ...],
        effects: tuple[EffectSite, ...],
        significance: SignificanceResult,
    ) -> FlowGraph:
        components = ComponentIndex(index)
        parallel_sites = ParallelDetector(index).detect(callsites)
        anchors = AnchorIndex(
            index, components, significance, callsites, dispatch_sites, effects, parallel_sites
        )
        acc = GraphAccumulator()
        summarizer = FunctionSummarizer(
            index, anchors, EventCollector(index, anchors), acc, self._labels, self._roots
        )
        entries = EntryFinder(
            index, RouteHandlerLocator(index), self._roots, self._labels
        ).find(dispatch_sites)
        self._assemble(acc, summarizer, entries, index)
        entries = TrivialEntryFolder(self._labels).fold(acc, entries)
        ancestry = CallAncestryResolver(callsites)
        anchor = AnchorResolver(self._roots, self._labels, ancestry, components)
        seeded = DecisionSeeder(index, anchor).seed(acc, summarizer, significance, entries)
        ContainerAssigner().assign(acc)
        StepMerger(acc, self._labels, ContainerRepointer()).merge()
        islanded = IslandAnchor(anchor).anchor(acc, entries + seeded)
        lanes = LaneBuilder(self._roots, self._labels).build(
            entries + seeded + islanded, dispatch_sites, significance
        )
        return FlowGraph(
            repo=repo,
            lanes=lanes,
            nodes=acc.to_flow_nodes(),
            edges=acc.to_flow_edges(),
            meta={"entries": len(entries), "lanes": len(lanes)},
        )

    def _assemble(
        self, acc: GraphAccumulator, summarizer: FunctionSummarizer,
        entries: tuple, index: ProjectIndex,
    ) -> None:
        for entry in entries:
            handlers = entry.members or (entry.handler_fqn,)
            refs = [index.functions[h].span for h in handlers if h in index.functions]
            folded = entry.route_count if entry.route_count > 1 else 0
            acc.upsert(
                entry.id, "entry", entry.service_root, entry.label,
                refs=refs or None, folded_count=folded,
            )
            for handler in handlers:
                summary = summarizer.summarize(handler)
                if summary.head is not None:
                    acc.connect(entry.id, summary.head, "sequence")
                    acc.add_container(summary.head, entry.id)

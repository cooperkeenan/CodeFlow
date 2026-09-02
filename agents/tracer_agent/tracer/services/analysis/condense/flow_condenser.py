from tracer.models.call_records import CallSite
from tracer.models.index_records import ProjectIndex
from tracer.models.sites import DispatchSite, EffectSite
from tracer.models.verdicts import SignificanceResult
from tracer.services.analysis.budget.container_repointer import ContainerRepointer
from tracer.services.analysis.condense.anchor_index import AnchorIndex
from tracer.services.analysis.condense.anchor_resolver import AnchorResolver
from tracer.services.analysis.condense.container_assigner import ContainerAssigner
from tracer.services.analysis.condense.decision_seeder import DecisionSeeder
from tracer.services.analysis.condense.event_collector import EventCollector
from tracer.services.analysis.condense.function_summarizer import FunctionSummarizer
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.condense.island_anchor import IslandAnchor
from tracer.services.analysis.condense.lane_builder import LaneBuilder
from tracer.services.analysis.condense.parallel_detector import ParallelDetector
from tracer.services.analysis.condense.step_merger import StepMerger
from tracer.services.analysis.condense.trivial_entry_folder import TrivialEntryFolder
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.resolve.call_ancestry_resolver import CallAncestryResolver
from tracer.services.analysis.resolve.indexes import ComponentIndex
from tracer.services.analysis.routes.entry_finder import EntryFinder
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer
from tracer.services.analysis.routes.route_handler_locator import RouteHandlerLocator

from shared.models.flow_graph import FlowGraph


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

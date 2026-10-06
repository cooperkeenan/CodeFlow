from tracer.models.call_records import CallSite
from tracer.models.index_records import ProjectIndex
from tracer.models.sites import DispatchSite, EffectSite
from tracer.models.verdicts import SignificanceResult
from tracer.services.analysis.budget.container_repointer import ContainerRepointer
from tracer.services.analysis.condense.anchor_index import AnchorIndex
from tracer.services.analysis.condense.anchor_resolver import AnchorResolver
from tracer.services.analysis.condense.container_assigner import ContainerAssigner
from tracer.services.analysis.condense.decision_seeder import DecisionSeeder
from tracer.services.analysis.condense.draft_exporter import DraftExporter
from tracer.services.analysis.condense.event_collector import EventCollector
from tracer.services.analysis.condense.function_summarizer import FunctionSummarizer
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.condense.island_anchor import IslandAnchor
from tracer.services.analysis.condense.lane_builder import LaneBuilder
from tracer.services.analysis.condense.parallel_detector import ParallelDetector
from tracer.services.analysis.condense.route_assembler import RouteAssembler
from tracer.services.analysis.condense.route_terminal_builder import (
    RouteTerminalBuilder,
)
from tracer.services.analysis.condense.step_merger import StepMerger
from tracer.services.analysis.condense.trivial_entry_folder import TrivialEntryFolder
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.resolve.call_ancestry_resolver import CallAncestryResolver
from tracer.services.analysis.resolve.indexes import ComponentIndex
from tracer.services.analysis.resolve.mro_method_finder import MroMethodFinder
from tracer.services.analysis.routes.delegation_resolver import DelegationResolver
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
        assembler = RouteAssembler(
            index, acc, summarizer,
            RouteTerminalBuilder(index, acc, self._labels, self._roots),
            DelegationResolver(index, MroMethodFinder(index)),
        )
        entries = assembler.assemble(entries)
        entries = TrivialEntryFolder(self._labels, ContainerRepointer()).fold(acc, entries)
        ancestry = CallAncestryResolver(callsites)
        anchor = AnchorResolver(self._roots, self._labels, ancestry, components)
        seeded = DecisionSeeder(index, anchor).seed(acc, summarizer, significance, entries)
        ContainerAssigner().assign(acc)
        StepMerger(acc, self._labels, ContainerRepointer(), self._heads(entries)).merge()
        islanded = IslandAnchor(anchor).anchor(acc, entries + seeded)
        lanes = LaneBuilder(self._roots, self._labels).build(
            entries + seeded + islanded, dispatch_sites, significance
        )
        exporter = DraftExporter()
        return FlowGraph(
            repo=repo,
            lanes=lanes,
            nodes=exporter.nodes(list(acc.nodes().values())),
            edges=exporter.edges(list(acc.edges().values())),
            meta={"entries": len(entries), "lanes": len(lanes)},
        )

    def _heads(self, entries: tuple) -> frozenset[str]:
        return frozenset(
            member.head for entry in entries for member in entry.route_members if member.head
        )

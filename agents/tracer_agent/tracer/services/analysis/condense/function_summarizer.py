from tracer.models.flow_summary import FlowSummary
from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.condense.anchor_index import AnchorIndex
from tracer.services.analysis.condense.event_collector import EventCollector
from tracer.services.analysis.condense.function_projector import FunctionProjector
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer


class FunctionSummarizer:
    def __init__(
        self,
        index: ProjectIndex,
        anchors: AnchorIndex,
        collector: EventCollector,
        acc: GraphAccumulator,
        labels: LabelSynthesizer,
        roots: ServiceRootResolver,
    ) -> None:
        self._index = index
        self._collector = collector
        self._roots = roots
        self._memo: dict[str, FlowSummary] = {}
        self._stack: set[str] = set()
        self._projector = FunctionProjector(index, anchors, acc, labels, self.summarize)

    def summarize(self, fqn: str) -> FlowSummary:
        if fqn in self._memo:
            return self._memo[fqn]
        if fqn not in self._index.functions:
            return FlowSummary(None, ())
        if fqn in self._stack:
            return FlowSummary(None, (), recursive=True)
        self._stack.add(fqn)
        events = self._collector.collect(fqn)
        summary = self._projector.project(fqn, events, self._roots.root_of(fqn))
        self._stack.discard(fqn)
        self._memo[fqn] = summary
        return summary

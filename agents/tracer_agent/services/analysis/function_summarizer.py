from models.flow_summary import FlowSummary
from models.project_index import ProjectIndex
from services.analysis.anchor_index import AnchorIndex
from services.analysis.event_collector import EventCollector
from services.analysis.function_projector import FunctionProjector
from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.service_root_resolver import ServiceRootResolver


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

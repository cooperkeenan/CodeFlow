from dataclasses import dataclass
from typing import Protocol

from tracer.models.call_records import CallSite
from tracer.models.index_records import ProjectIndex
from tracer.models.sites import DispatchSite, EffectSite, FlowEntry
from tracer.models.verdicts import DecisionCandidate, DecisionVerdict

from shared.models.flow_graph import FlowEdge, FlowGraph


class DecisionJudge(Protocol):
    def judge(self, candidates: tuple[DecisionCandidate, ...]) -> dict[str, DecisionVerdict]: ...


class FlowNaming(Protocol):
    def name(self, graph: FlowGraph) -> FlowGraph: ...


class FlowReviewing(Protocol):
    def review(self, graph: FlowGraph) -> FlowGraph: ...


class StitchDetector(Protocol):
    def detect(
        self, effects: tuple[EffectSite, ...], entries: tuple[FlowEntry, ...]
    ) -> tuple[FlowEdge, ...]: ...


@dataclass(frozen=True)
class DispatchDetectionContext:
    index: ProjectIndex
    callsites: tuple[CallSite, ...]


class RouteFrameworkScanner(Protocol):
    def scan(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]: ...

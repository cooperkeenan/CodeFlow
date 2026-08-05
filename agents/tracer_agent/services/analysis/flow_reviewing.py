from typing import Protocol

from shared.models.flow_graph import FlowGraph


class FlowReviewing(Protocol):
    def review(self, graph: FlowGraph) -> FlowGraph: ...

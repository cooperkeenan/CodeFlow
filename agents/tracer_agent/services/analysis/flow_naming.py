from typing import Protocol

from shared.models.flow_graph import FlowGraph


class FlowNaming(Protocol):
    def name(self, graph: FlowGraph) -> FlowGraph: ...

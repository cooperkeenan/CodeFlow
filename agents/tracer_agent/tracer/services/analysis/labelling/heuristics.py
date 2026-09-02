from shared.models.flow_graph import FlowGraph


class HeuristicFlowNamer:
    def name(self, graph: FlowGraph) -> FlowGraph:
        return graph


class HeuristicFlowReviewer:
    def review(self, graph: FlowGraph) -> FlowGraph:
        return graph

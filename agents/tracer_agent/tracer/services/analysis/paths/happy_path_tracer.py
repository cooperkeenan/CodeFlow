from tracer.services.analysis.paths.happy_path_walker import HappyPathWalker

from shared.models.flow_graph import FlowGraph, FlowNode

_SEED_PREFIX = "entry:seed:"


class HappyPathTracer:
    def __init__(self, walker: HappyPathWalker) -> None:
        self._walker = walker

    def trace(self, graph: FlowGraph) -> FlowGraph:
        nodes = [self._with_paths(n) if self._is_route_entry(n) else n for n in graph.nodes]
        return graph.model_copy(update={"nodes": nodes})

    def _is_route_entry(self, node: FlowNode) -> bool:
        return node.kind == "entry" and bool(node.members) and not node.id.startswith(_SEED_PREFIX)

    def _with_paths(self, node: FlowNode) -> FlowNode:
        members = [
            m.model_copy(update={"happy": self._walker.walk(node.id, m)}) for m in node.members
        ]
        return node.model_copy(update={"members": members})

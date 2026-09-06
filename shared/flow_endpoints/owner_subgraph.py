from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.models.flow_graph import FlowGraph, FlowNode


class OwnerSubgraph:
    def __init__(self, endpoint_subgraph: EndpointSubgraph) -> None:
        self._endpoint_subgraph = endpoint_subgraph

    def slice(self, graph: FlowGraph, owner_fqn: str) -> FlowGraph | None:
        members = [node for node in graph.nodes if node.owner_fqn == owner_fqn]
        if not members:
            return None
        member_ids = {node.id for node in members}
        predecessors: dict[str, set[str]] = {node.id: set() for node in members}
        for edge in graph.edges:
            if edge.source in member_ids and edge.target in member_ids:
                predecessors[edge.target].add(edge.source)
        heads = [node for node in members if not predecessors[node.id]]
        pool = heads or members
        head = min(pool, key=self._tie_break)
        return self._endpoint_subgraph.slice_root(graph, head.id)

    def _tie_break(self, node: FlowNode) -> tuple[str, int, str]:
        if node.refs:
            return (node.refs[0].file, node.refs[0].line, node.id)
        return ("", 0, node.id)

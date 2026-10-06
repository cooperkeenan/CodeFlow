from collections.abc import Iterator

from shared.flow_endpoints.route_subgraph import RouteSubgraph
from shared.models.flow_graph import FlowGraph, FlowNode


class RouteFixtureSlices:
    def __init__(self, routes: RouteSubgraph) -> None:
        self._routes = routes

    def slices(self, graph: FlowGraph, node: FlowNode) -> Iterator[tuple[str, FlowGraph]]:
        if node.kind != "entry":
            return
        for member in sorted(node.members, key=lambda m: (m.path, m.method, m.handler_fqn)):
            sliced = self._routes.slice(graph, node.id, member.handler_fqn)
            if sliced is not None:
                yield member.handler_fqn, sliced

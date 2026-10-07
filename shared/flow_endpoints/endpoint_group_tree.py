import re

from shared.flow_endpoints.endpoint_group import EndpointGroup, GroupForest, GroupRoute
from shared.flow_endpoints.entry_routes import EntryRoutes
from shared.flow_endpoints.group_splitter import GroupSplitter
from shared.models.flow_graph import FlowGraph, FlowNode

_SEED_PREFIX = "entry:seed:"
_ROUTE_COUNT = re.compile(r"\s*·\s*\d+ routes?.*$")


class EndpointGroupTree:
    def __init__(self, splitter: GroupSplitter, routes: EntryRoutes) -> None:
        self._splitter = splitter
        self._routes = routes

    def build(self, graph: FlowGraph) -> GroupForest:
        roots = sorted((n for n in graph.nodes if self._is_route_entry(n)), key=lambda n: n.id)
        groups: list[EndpointGroup] = []
        for node in roots:
            routes = [GroupRoute(m.handler_fqn, m.method, m.path) for m in self._routes.of(node)]
            groups.extend(
                self._splitter.split(node.id, self._name(node), node.id, routes, 0)
            )
        return GroupForest(tuple(groups))

    def _name(self, node: FlowNode) -> str:
        return _ROUTE_COUNT.sub("", node.llm_label or node.label) or node.label

    def _is_route_entry(self, node: FlowNode) -> bool:
        return node.kind == "entry" and bool(node.members) and not node.id.startswith(_SEED_PREFIX)

from shared.flow_endpoints.route_label import RouteLabel
from shared.models.flow_graph import FlowNode, RouteMember


class EntryRoutes:
    def __init__(self, route_label: RouteLabel | None = None) -> None:
        self._route_label = route_label or RouteLabel()

    def of(self, node: FlowNode) -> list[RouteMember]:
        if node.members:
            return sorted(node.members, key=lambda m: (m.path, m.method, m.handler_fqn))
        method, path = self._route_label.parse(node.label)
        return [RouteMember(handler_fqn="", method=method, path=path)]

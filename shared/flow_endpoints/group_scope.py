from shared.flow_endpoints.route_scope import RouteScope, RouteScopeResult
from shared.models.flow_graph import FlowEdge, FlowNode, RouteMember


class GroupScope:
    def __init__(self, scope: RouteScope) -> None:
        self._scope = scope

    def of(
        self,
        nodes: dict[str, FlowNode],
        edges: list[FlowEdge],
        root: FlowNode,
        members: list[RouteMember],
    ) -> RouteScopeResult:
        walked = [m for m in members if m.happy is not None and m.happy.node_ids]
        hops = {h for m in walked for h in m.happy.hops}
        others = frozenset(
            i for m in walked for i in m.happy.node_ids if i in nodes and i not in hops
        )
        ids: set[str] = {root.id}
        regions: dict[str, list[str]] = {}
        for member in walked:
            result = self._scope.of(nodes, edges, root, member, others, frozenset(hops) - set(member.happy.hops))
            ids |= result.ids
            for hop, region in result.regions.items():
                regions[hop] = sorted(set(regions.get(hop, [])) | set(region))
        return RouteScopeResult(ids, regions)

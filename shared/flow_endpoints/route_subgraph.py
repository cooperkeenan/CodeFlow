from shared.flow_endpoints.endpoint_elider import EndpointElider
from shared.flow_endpoints.entry_routes import EntryRoutes
from shared.flow_endpoints.happy_payload import HappyPayload
from shared.flow_endpoints.hop_collapser import HopCollapser
from shared.flow_endpoints.route_scope import RouteScope
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.flow_endpoints.slice_assembler import SliceAssembler
from shared.models.flow_graph import FlowGraph


class RouteSubgraph:
    def __init__(
        self,
        assembler: SliceAssembler,
        elider: EndpointElider,
        scope: RouteScope,
        hops: HopCollapser,
        payload: HappyPayload,
        owners: SharedOwnerIndex,
        routes: EntryRoutes,
    ) -> None:
        self._assembler = assembler
        self._elider = elider
        self._scope = scope
        self._hops = hops
        self._payload = payload
        self._owners = owners
        self._routes = routes

    def slice(self, graph: FlowGraph, entry_id: str, handler_fqn: str) -> FlowGraph | None:
        nodes_by_id = {node.id: node for node in graph.nodes}
        root = nodes_by_id.get(entry_id)
        if root is None or root.kind != "entry":
            return None
        member = self._routes.member(root, handler_fqn)
        if member is None or member.happy is None or not member.happy.node_ids:
            return None
        path = member.happy.node_ids
        scoped = self._scope.of(nodes_by_id, graph.edges, root, member)
        working = self._assembler.working(graph, nodes_by_id, scoped.ids, entry_id, path)
        self._hops.collapse(
            working, scoped.regions, path, [h for h in path if h in member.happy.hops]
        )
        self._elider.elide(
            working,
            self._owners.counts(graph),
            self._assembler.closer(graph, nodes_by_id),
            pins=path,
        )
        meta = {
            "entry_id": entry_id,
            "entry_label": root.label,
            "route": {"handler_fqn": member.handler_fqn, "method": member.method, "path": member.path},
            "happy": self._payload.build(working, member.happy.ends_in_failure),
            "visible_before_promote": working.visible_before_promote,
        }
        return self._assembler.finish(graph, working, root, meta)

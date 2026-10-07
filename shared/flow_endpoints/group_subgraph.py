from itertools import pairwise

from shared.flow_endpoints.back_edge_pruner import BackEdgePruner
from shared.flow_endpoints.endpoint_elider import EndpointElider
from shared.flow_endpoints.endpoint_group import EndpointGroup, GroupForest
from shared.flow_endpoints.group_meta import GroupMeta
from shared.flow_endpoints.group_paths import GroupPaths
from shared.flow_endpoints.group_scope import GroupScope
from shared.flow_endpoints.hop_collapser import HopCollapser
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.flow_endpoints.slice_assembler import SliceAssembler
from shared.flow_endpoints.slice_graph import SliceGraph
from shared.models.flow_graph import FlowGraph, FlowNode, RouteMember


class GroupSubgraph:
    def __init__(
        self,
        assembler: SliceAssembler,
        elider: EndpointElider,
        scope: GroupScope,
        hops: HopCollapser,
        paths: GroupPaths,
        owners: SharedOwnerIndex,
        meta: GroupMeta,
        pruner: BackEdgePruner,
    ) -> None:
        self._pruner = pruner
        self._assembler = assembler
        self._elider = elider
        self._scope = scope
        self._hops = hops
        self._paths = paths
        self._owners = owners
        self._meta = meta

    def slice(self, graph: FlowGraph, forest: GroupForest, group_id: str) -> FlowGraph | None:
        group = forest.find(group_id)
        if group is None or not group.is_leaf:
            return None
        nodes_by_id = {node.id: node for node in graph.nodes}
        root = nodes_by_id.get(group.entry_id)
        if root is None or root.kind != "entry":
            return None
        members = self._members(root, group)
        walked = [m for m in members if m.happy is not None and m.happy.node_ids]
        scoped = self._scope.of(nodes_by_id, graph.edges, root, members)
        pairs = {pair for m in walked for pair in pairwise(m.happy.node_ids)}
        working = self._assembler.working(
            graph, nodes_by_id, scoped.ids, root.id, pairs, self._sealed(scoped.regions)
        )
        routes = [
            (m.happy.node_ids, [h for h in m.happy.node_ids if h in m.happy.hops]) for m in walked
        ]
        self._hops.collapse(working, scoped.regions, routes)
        self._prune(working, walked)
        working.set_protected([i for m in walked for i in m.happy.node_ids])
        self._elider.elide(
            working, self._owners.counts(graph), self._assembler.closer(graph, nodes_by_id)
        )
        title = self._meta.title(group)
        view_root = working.nodes[root.id]
        working.nodes[root.id] = view_root.model_copy(update=self._meta.root_fields(group, view_root))
        meta = {
            "entry_id": root.id,
            "entry_label": title,
            "group": self._meta.of(group),
            "paths": self._paths.build(working, members),
            "visible_before_promote": working.visible_before_promote,
        }
        return self._assembler.finish(graph, working, working.nodes[root.id], meta)

    def _members(self, root: FlowNode, group: EndpointGroup) -> list[RouteMember]:
        wanted = {(r.handler_fqn, r.method, r.path) for r in group.routes}
        return [m for m in root.members if (m.handler_fqn, m.method, m.path) in wanted]

    def _prune(self, working: SliceGraph, walked: list[RouteMember]) -> None:
        pairs = {
            pair for m in walked for pair in pairwise(working.resolve_path(m.happy.node_ids))
        }
        working.edges = self._pruner.prune(set(working.nodes), working.edges, working.root_id, pairs)

    def _sealed(self, regions: dict[str, list[str]]) -> dict[str, frozenset[str]]:
        owned: dict[str, set[str]] = {}
        for region in regions.values():
            for node_id in region:
                if node_id not in regions:
                    owned.setdefault(node_id, set()).update(region)
        sealed = {node_id: frozenset(members) for node_id, members in owned.items()}
        sealed.update({hop: frozenset(region) for hop, region in regions.items()})
        return sealed

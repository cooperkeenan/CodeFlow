from shared.flow_endpoints.chunk_dissolver import ChunkDissolver
from shared.flow_endpoints.endpoint_elider import EndpointElider
from shared.flow_endpoints.endpoint_group_tree import EndpointGroupTree
from shared.flow_endpoints.entry_routes import EntryRoutes
from shared.flow_endpoints.group_splitter import GroupSplitter
from shared.flow_endpoints.happy_payload import HappyPayload
from shared.flow_endpoints.hop_collapser import HopCollapser
from shared.flow_endpoints.level_assigner import LevelAssigner
from shared.flow_endpoints.route_scope import RouteScope
from shared.flow_endpoints.route_subgraph import RouteSubgraph
from shared.flow_endpoints.shared_helper_collapser import SharedHelperCollapser
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.flow_endpoints.slice_assembler import SliceAssembler


def build_route_subgraph() -> RouteSubgraph:
    helpers = SharedHelperCollapser()
    return RouteSubgraph(
        SliceAssembler(),
        EndpointElider(ChunkDissolver(), LevelAssigner(), helpers=helpers),
        RouteScope(),
        HopCollapser(helpers),
        HappyPayload(),
        SharedOwnerIndex(),
        EntryRoutes(),
    )


def build_group_tree() -> EndpointGroupTree:
    return EndpointGroupTree(GroupSplitter(), EntryRoutes())

from fastapi import Depends

from gateway.clients.render_client import RenderClient
from gateway.deps.clients import get_render_client
from gateway.deps.services import get_repo_map_service
from gateway.deps.stores import get_endpoint_view_cache, get_flow_graph_cache
from gateway.services.endpoint_view_cache import EndpointViewCache
from gateway.services.endpoint_view_service import EndpointViewService
from gateway.services.flow_graph_cache import FlowGraphCache
from gateway.services.repo_map_service import RepoMapService
from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.flow_endpoints.link_resolver import LinkResolver
from shared.flow_endpoints.owner_subgraph import OwnerSubgraph
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex


def get_endpoint_view_service(
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    render_client: RenderClient = Depends(get_render_client),
    graph_cache: FlowGraphCache = Depends(get_flow_graph_cache),
    view_cache: EndpointViewCache = Depends(get_endpoint_view_cache),
) -> EndpointViewService:
    subgraph = EndpointSubgraph()
    return EndpointViewService(
        repo_map_service,
        render_client,
        EndpointCatalog(),
        subgraph,
        OwnerSubgraph(subgraph),
        SharedOwnerIndex(),
        LinkResolver(),
        graph_cache,
        view_cache,
    )

from fastapi import Depends

from gateway.clients.explain_client import ExplainClient
from gateway.clients.render_client import RenderClient
from gateway.deps.clients import get_explain_client, get_render_client
from gateway.deps.services import get_repo_map_service, get_symbol_context_resolver
from gateway.deps.stores import (
    get_endpoint_view_cache,
    get_explanation_store,
    get_flow_graph_cache,
)
from gateway.services.endpoint_contract_resolver import EndpointContractResolver
from gateway.services.endpoint_detail_service import EndpointDetailService
from gateway.services.endpoint_view_cache import EndpointViewCache
from gateway.services.endpoint_view_service import EndpointViewService
from gateway.services.flow_graph_cache import FlowGraphCache
from gateway.services.flow_graph_loader import FlowGraphLoader
from gateway.services.flow_payload_service import FlowPayloadService
from gateway.services.flow_view_renderer import FlowViewRenderer
from gateway.services.repo_map_service import RepoMapService
from gateway.services.route_view_service import RouteViewService
from gateway.services.symbol_context_resolver import SymbolContextResolver
from shared.explanation_store.explanation_store import ExplanationStore
from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_detail_builder import EndpointDetailBuilder
from shared.flow_endpoints.endpoint_key_methods import KeyMethodSelector
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.flow_endpoints.factory import build_route_subgraph
from shared.flow_endpoints.link_resolver import LinkResolver
from shared.flow_endpoints.owner_subgraph import OwnerSubgraph
from shared.flow_endpoints.route_label import RouteLabel
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex


def get_flow_graph_loader(
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    graph_cache: FlowGraphCache = Depends(get_flow_graph_cache),
) -> FlowGraphLoader:
    return FlowGraphLoader(repo_map_service, graph_cache)


def get_flow_view_renderer(
    render_client: RenderClient = Depends(get_render_client),
) -> FlowViewRenderer:
    return FlowViewRenderer(render_client, SharedOwnerIndex(), LinkResolver())


def get_endpoint_view_service(
    loader: FlowGraphLoader = Depends(get_flow_graph_loader),
    renderer: FlowViewRenderer = Depends(get_flow_view_renderer),
    view_cache: EndpointViewCache = Depends(get_endpoint_view_cache),
) -> EndpointViewService:
    subgraph = EndpointSubgraph()
    return EndpointViewService(
        loader,
        renderer,
        EndpointCatalog(),
        subgraph,
        OwnerSubgraph(subgraph),
        view_cache,
    )


def get_route_view_service(
    loader: FlowGraphLoader = Depends(get_flow_graph_loader),
    renderer: FlowViewRenderer = Depends(get_flow_view_renderer),
    view_cache: EndpointViewCache = Depends(get_endpoint_view_cache),
) -> RouteViewService:
    return RouteViewService(loader, renderer, build_route_subgraph(), view_cache)


def get_flow_payload_service(
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    endpoints: EndpointViewService = Depends(get_endpoint_view_service),
    routes: RouteViewService = Depends(get_route_view_service),
) -> FlowPayloadService:
    return FlowPayloadService(repo_map_service, endpoints, routes)


def get_endpoint_detail_service(
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    resolver: SymbolContextResolver = Depends(get_symbol_context_resolver),
    explain_client: ExplainClient = Depends(get_explain_client),
    explanation_store: ExplanationStore = Depends(get_explanation_store),
    graph_cache: FlowGraphCache = Depends(get_flow_graph_cache),
    view_cache: EndpointViewCache = Depends(get_endpoint_view_cache),
) -> EndpointDetailService:
    return EndpointDetailService(
        repo_map_service,
        resolver,
        EndpointContractResolver(explain_client, explanation_store),
        graph_cache,
        view_cache,
        KeyMethodSelector(EndpointSubgraph()),
        RouteLabel(),
        EndpointDetailBuilder(RouteLabel()),
    )

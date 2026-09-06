import dataclasses
from datetime import datetime

from gateway.clients.render_client import RenderClient
from gateway.models.repo_map_model import EndpointSummary, RepoHomeResponse
from gateway.services.endpoint_view_cache import EndpointViewCache
from gateway.services.flow_graph_cache import FlowGraphCache
from gateway.services.repo_map_service import RepoMapService

from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_items import EndpointItem
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.flow_endpoints.link_resolver import LinkResolver
from shared.flow_endpoints.owner_subgraph import OwnerSubgraph
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.models.flow_graph import FlowGraph

_HOME_VIEW_KEY = "home"


class EndpointViewService:
    def __init__(
        self,
        repo_maps: RepoMapService,
        render_client: RenderClient,
        catalog: EndpointCatalog,
        subgraph: EndpointSubgraph,
        owner_subgraph: OwnerSubgraph,
        owner_index: SharedOwnerIndex,
        link_resolver: LinkResolver,
        graph_cache: FlowGraphCache,
        view_cache: EndpointViewCache,
    ) -> None:
        self._repo_maps = repo_maps
        self._render = render_client
        self._catalog = catalog
        self._subgraph = subgraph
        self._owner_subgraph = owner_subgraph
        self._owner_index = owner_index
        self._link_resolver = link_resolver
        self._graph_cache = graph_cache
        self._view_cache = view_cache

    async def home(self, user_id: int, repo: str) -> RepoHomeResponse | None:
        resolved = await self._resolve(user_id, repo)
        if resolved is None:
            return None
        graph, updated_at = resolved
        cached = self._view_cache.get(user_id, repo, updated_at, _HOME_VIEW_KEY)
        if cached is not None:
            return RepoHomeResponse.model_validate(cached)
        items = self._catalog.items(graph)
        response = RepoHomeResponse(
            repo=repo,
            title=graph.repo or repo,
            description=graph.page_title,
            endpoints=[self._summary(i) for i in items if i.is_route],
            entry_points=[self._summary(i) for i in items if not i.is_route],
        )
        self._view_cache.put(
            user_id, repo, updated_at, _HOME_VIEW_KEY, response.model_dump(mode="json")
        )
        return response

    async def view(self, user_id: int, repo: str, entry_id: str) -> dict | None:
        resolved = await self._resolve(user_id, repo)
        if resolved is None:
            return None
        graph, updated_at = resolved
        view_key = f"entry:{entry_id}"
        cached = self._view_cache.get(user_id, repo, updated_at, view_key)
        if cached is not None:
            return cached
        sliced = self._subgraph.slice(graph, entry_id)
        if sliced is None:
            return None
        result = await self._rendered(repo, sliced, graph, entry_id)
        self._view_cache.put(user_id, repo, updated_at, view_key, result)
        return result

    async def helper_view(self, user_id: int, repo: str, owner_fqn: str) -> dict | None:
        resolved = await self._resolve(user_id, repo)
        if resolved is None:
            return None
        graph, updated_at = resolved
        view_key = f"helper:{owner_fqn}"
        cached = self._view_cache.get(user_id, repo, updated_at, view_key)
        if cached is not None:
            return cached
        sliced = self._owner_subgraph.slice(graph, owner_fqn)
        if sliced is None:
            return None
        result = await self._rendered(repo, sliced, graph, owner_fqn)
        self._view_cache.put(user_id, repo, updated_at, view_key, result)
        return result

    async def _rendered(
        self, repo: str, sliced: FlowGraph, graph: FlowGraph, current_root: str
    ) -> dict:
        rendered = await self._render.render(sliced.model_dump(mode="json"), lane_headers=False)
        owners = self._owner_index.owners(graph)
        links = self._link_resolver.resolve(sliced, owners, current_root)
        return {
            "page_title": sliced.page_title,
            "repo": repo,
            "repo_url": "",
            "view": rendered["view"],
            "links": {node_id: dataclasses.asdict(link) for node_id, link in links.items()},
        }

    async def _resolve(self, user_id: int, repo: str) -> tuple[FlowGraph, datetime] | None:
        updated_at = await self._repo_maps.updated_at(user_id, repo)
        if updated_at is None:
            return None
        graph = await self._graph(user_id, repo, updated_at)
        if graph is None:
            return None
        return graph, updated_at

    async def _graph(self, user_id: int, repo: str, updated_at: datetime) -> FlowGraph | None:
        cached = self._graph_cache.get(user_id, repo, updated_at)
        if cached is not None:
            return cached
        detail = await self._repo_maps.get(user_id, repo)
        if detail is None:
            return None
        payload = detail.map.trace.get("flow_graph")
        graph = FlowGraph.model_validate(payload) if payload else None
        if graph is not None:
            self._graph_cache.put(user_id, repo, updated_at, graph)
        return graph

    def _summary(self, item: EndpointItem) -> EndpointSummary:
        return EndpointSummary(
            id=item.id,
            label=item.label,
            title=item.title,
            one_liner=item.one_liner,
            route_count=item.route_count,
            file=item.file,
            line=item.line,
        )

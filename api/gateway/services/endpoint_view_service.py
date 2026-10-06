from gateway.models.repo_map_model import EndpointSummary, RepoHomeResponse
from gateway.services.endpoint_view_cache import EndpointViewCache
from gateway.services.flow_graph_loader import FlowGraphLoader
from gateway.services.flow_view_renderer import FlowViewRenderer

from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_items import EndpointItem
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.flow_endpoints.owner_subgraph import OwnerSubgraph

_HOME_VIEW_KEY = "home"


class EndpointViewService:
    def __init__(
        self,
        loader: FlowGraphLoader,
        renderer: FlowViewRenderer,
        catalog: EndpointCatalog,
        subgraph: EndpointSubgraph,
        owner_subgraph: OwnerSubgraph,
        view_cache: EndpointViewCache,
    ) -> None:
        self._loader = loader
        self._renderer = renderer
        self._catalog = catalog
        self._subgraph = subgraph
        self._owner_subgraph = owner_subgraph
        self._view_cache = view_cache

    async def home(self, user_id: int, repo: str) -> RepoHomeResponse | None:
        resolved = await self._loader.load(user_id, repo)
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
        resolved = await self._loader.load(user_id, repo)
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
        result = await self._renderer.render(repo, sliced, graph, entry_id)
        self._view_cache.put(user_id, repo, updated_at, view_key, result)
        return result

    async def helper_view(self, user_id: int, repo: str, owner_fqn: str) -> dict | None:
        resolved = await self._loader.load(user_id, repo)
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
        result = await self._renderer.render(repo, sliced, graph, owner_fqn)
        self._view_cache.put(user_id, repo, updated_at, view_key, result)
        return result

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

from gateway.clients.render_client import RenderClient
from gateway.models.repo_map_model import EndpointSummary, RepoHomeResponse
from gateway.services.repo_map_service import RepoMapService

from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_items import EndpointItem
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.models.flow_graph import FlowGraph


class EndpointViewService:
    def __init__(
        self,
        repo_maps: RepoMapService,
        render_client: RenderClient,
        catalog: EndpointCatalog,
        subgraph: EndpointSubgraph,
    ) -> None:
        self._repo_maps = repo_maps
        self._render = render_client
        self._catalog = catalog
        self._subgraph = subgraph

    async def home(self, user_id: int, repo: str) -> RepoHomeResponse | None:
        graph = await self._graph(user_id, repo)
        if graph is None:
            return None
        items = self._catalog.items(graph)
        return RepoHomeResponse(
            repo=repo,
            title=graph.repo or repo,
            description=graph.page_title,
            endpoints=[self._summary(i) for i in items if i.is_route],
            entry_points=[self._summary(i) for i in items if not i.is_route],
        )

    async def view(self, user_id: int, repo: str, entry_id: str) -> dict | None:
        graph = await self._graph(user_id, repo)
        if graph is None:
            return None
        sliced = self._subgraph.slice(graph, entry_id)
        if sliced is None:
            return None
        rendered = await self._render.render(sliced.model_dump(mode="json"), lane_headers=False)
        return {
            "page_title": sliced.page_title,
            "repo": repo,
            "repo_url": "",
            "view": rendered["view"],
        }

    async def _graph(self, user_id: int, repo: str) -> FlowGraph | None:
        detail = await self._repo_maps.get(user_id, repo)
        if detail is None:
            return None
        payload = detail.map.trace.get("flow_graph")
        return FlowGraph.model_validate(payload) if payload else None

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

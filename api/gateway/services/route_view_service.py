from gateway.services.endpoint_view_cache import EndpointViewCache
from gateway.services.flow_graph_loader import FlowGraphLoader
from gateway.services.flow_view_renderer import FlowViewRenderer

from shared.flow_endpoints.route_subgraph import RouteSubgraph


class RouteViewService:
    def __init__(
        self,
        loader: FlowGraphLoader,
        renderer: FlowViewRenderer,
        subgraph: RouteSubgraph,
        view_cache: EndpointViewCache,
    ) -> None:
        self._loader = loader
        self._renderer = renderer
        self._subgraph = subgraph
        self._view_cache = view_cache

    async def view(self, user_id: int, repo: str, entry_id: str, handler_fqn: str) -> dict | None:
        loaded = await self._loader.load(user_id, repo)
        if loaded is None:
            return None
        graph, updated_at = loaded
        view_key = f"route:{entry_id}|{handler_fqn}"
        cached = self._view_cache.get(user_id, repo, updated_at, view_key)
        if cached is not None:
            return cached
        sliced = self._subgraph.slice(graph, entry_id, handler_fqn)
        if sliced is None:
            return None
        result = await self._renderer.render(repo, sliced, graph, entry_id)
        result["route"] = sliced.meta["route"]
        result["happy"] = sliced.meta["happy"]
        self._view_cache.put(user_id, repo, updated_at, view_key, result)
        return result

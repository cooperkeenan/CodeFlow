from datetime import datetime

from gateway.services.flow_graph_cache import FlowGraphCache
from gateway.services.repo_map_service import RepoMapService

from shared.models.flow_graph import FlowGraph


class FlowGraphLoader:
    def __init__(self, repo_maps: RepoMapService, graph_cache: FlowGraphCache) -> None:
        self._repo_maps = repo_maps
        self._graph_cache = graph_cache

    async def load(self, user_id: int, repo: str) -> tuple[FlowGraph, datetime] | None:
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

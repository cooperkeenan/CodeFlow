from gateway.services.endpoint_view_cache import EndpointViewCache
from gateway.services.flow_graph_loader import FlowGraphLoader
from gateway.services.flow_view_renderer import FlowViewRenderer

from shared.flow_endpoints.endpoint_group_tree import EndpointGroupTree
from shared.flow_endpoints.group_overview import GroupOverview
from shared.flow_endpoints.group_subgraph import GroupSubgraph


class GroupViewService:
    def __init__(
        self,
        loader: FlowGraphLoader,
        renderer: FlowViewRenderer,
        tree: EndpointGroupTree,
        subgraph: GroupSubgraph,
        overview: GroupOverview,
        view_cache: EndpointViewCache,
    ) -> None:
        self._loader = loader
        self._renderer = renderer
        self._tree = tree
        self._subgraph = subgraph
        self._overview = overview
        self._view_cache = view_cache

    async def view(self, user_id: int, repo: str, group_id: str) -> dict | None:
        loaded = await self._loader.load(user_id, repo)
        if loaded is None:
            return None
        graph, updated_at = loaded
        view_key = f"group:{group_id}"
        cached = self._view_cache.get(user_id, repo, updated_at, view_key)
        if cached is not None:
            return cached
        forest = self._tree.build(graph)
        group = forest.find(group_id)
        if group is None:
            return None
        slicer = self._subgraph if group.is_leaf else self._overview
        sliced = slicer.slice(graph, forest, group_id)
        if sliced is None:
            return None
        result = await self._renderer.render(repo, sliced, graph, group.entry_id)
        result["group"] = sliced.meta["group"]
        result["paths"] = sliced.meta["paths"]
        self._view_cache.put(user_id, repo, updated_at, view_key, result)
        return result

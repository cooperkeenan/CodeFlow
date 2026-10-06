from fastapi import HTTPException
from gateway.services.endpoint_view_service import EndpointViewService
from gateway.services.repo_map_service import RepoMapService
from gateway.services.route_view_service import RouteViewService


class FlowPayloadService:
    def __init__(
        self,
        repo_maps: RepoMapService,
        endpoints: EndpointViewService,
        routes: RouteViewService,
    ) -> None:
        self._repo_maps = repo_maps
        self._endpoints = endpoints
        self._routes = routes

    async def payload(
        self,
        user_id: int,
        repo: str,
        entry: str | None,
        helper: str | None,
        route: str | None,
    ) -> dict:
        if helper:
            view = await self._endpoints.helper_view(user_id, repo, helper)
            if view is None:
                raise HTTPException(status_code=404, detail="Helper not found")
            return view
        if entry and route:
            view = await self._routes.view(user_id, repo, entry, route)
            if view is None:
                raise HTTPException(status_code=404, detail="Route not found")
            return view
        if entry:
            view = await self._endpoints.view(user_id, repo, entry)
            if view is None:
                raise HTTPException(status_code=404, detail="Endpoint not found")
            return view
        detail = await self._repo_maps.get(user_id, repo)
        if detail is None:
            raise HTTPException(status_code=404, detail="Repo map not found")
        flow_graph = detail.map.trace.get("flow_graph", {})
        return {
            "page_title": flow_graph.get("page_title", repo),
            "repo": repo,
            "repo_url": "",
            "view": detail.map.diagram.get("view", {}),
        }

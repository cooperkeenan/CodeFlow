from fastapi import APIRouter, Depends, HTTPException
from gateway.deps import (
    get_current_user,
    get_endpoint_view_service,
    get_node_explain_service,
    get_repo_map_service,
)
from gateway.models.auth_model import AuthUser
from gateway.models.repo_map_model import (
    NodeExplainRequest,
    RepoHomeResponse,
    RepoMapDetail,
    RepoMapListResponse,
)
from gateway.services.endpoint_view_service import EndpointViewService
from gateway.services.node_explain_service import NodeExplainService
from gateway.services.repo_map_service import RepoMapService

router = APIRouter(prefix="/repomaps", tags=["repomaps"])


@router.get("", response_model=RepoMapListResponse)
async def list_repo_maps(
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
) -> RepoMapListResponse:
    return RepoMapListResponse(repo_maps=await service.list(user.id))


@router.get("/{repo:path}/home", response_model=RepoHomeResponse)
async def get_repo_home(
    repo: str,
    user: AuthUser = Depends(get_current_user),
    endpoints: EndpointViewService = Depends(get_endpoint_view_service),
) -> RepoHomeResponse:
    home = await endpoints.home(user.id, repo)
    if home is None:
        raise HTTPException(status_code=404, detail="Repo map not found")
    return home


@router.get("/{repo:path}/flow")
async def get_repo_flow(
    repo: str,
    entry: str | None = None,
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
    endpoints: EndpointViewService = Depends(get_endpoint_view_service),
) -> dict:
    if entry:
        view = await endpoints.view(user.id, repo, entry)
        if view is None:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return view
    detail = await service.get(user.id, repo)
    if detail is None:
        raise HTTPException(status_code=404, detail="Repo map not found")
    flow_graph = detail.map.trace.get("flow_graph", {})
    view = detail.map.diagram.get("view", {})
    return {
        "page_title": flow_graph.get("page_title", repo),
        "repo": repo,
        "repo_url": "",
        "view": view,
    }


@router.post("/{repo:path}/explain")
async def explain_repo_node(
    repo: str,
    body: NodeExplainRequest,
    user: AuthUser = Depends(get_current_user),
    service: NodeExplainService = Depends(get_node_explain_service),
) -> dict:
    result = await service.explain(user.id, repo, body.node_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@router.get("/{repo:path}", response_model=RepoMapDetail)
async def get_repo_map(
    repo: str,
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
) -> RepoMapDetail:
    detail = await service.get(user.id, repo)
    if detail is None:
        raise HTTPException(status_code=404, detail="Repo map not found")
    return detail

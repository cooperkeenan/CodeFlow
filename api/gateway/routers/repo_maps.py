from fastapi import APIRouter, Depends, HTTPException
from gateway.deps import (
    get_current_user,
    get_node_explain_service,
    get_repo_map_service,
)
from gateway.models.auth_model import AuthUser
from gateway.models.repo_map_model import (
    NodeExplainRequest,
    RepoMapDetail,
    RepoMapListResponse,
)
from gateway.services.node_explain_service import NodeExplainService
from gateway.services.repo_map_service import RepoMapService

router = APIRouter(prefix="/repomaps", tags=["repomaps"])


@router.get("", response_model=RepoMapListResponse)
async def list_repo_maps(
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
) -> RepoMapListResponse:
    return RepoMapListResponse(repo_maps=await service.list(user.id))


@router.get("/{repo:path}/flow")
async def get_repo_flow(
    repo: str,
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
) -> dict:
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

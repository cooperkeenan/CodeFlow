from fastapi import APIRouter, Depends, HTTPException, Request, Response
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
from gateway.services.etag import ETag
from gateway.services.node_explain_service import NodeExplainService
from gateway.services.repo_map_service import RepoMapService

router = APIRouter(prefix="/repomaps", tags=["repomaps"])


@router.get("", response_model=RepoMapListResponse)
async def list_repo_maps(
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
) -> RepoMapListResponse:
    return RepoMapListResponse(repo_maps=await service.list(user.id))


@router.get("/{repo:path}/home", response_model=None)
async def get_repo_home(
    repo: str,
    request: Request,
    response: Response,
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
    endpoints: EndpointViewService = Depends(get_endpoint_view_service),
) -> RepoHomeResponse | Response:
    updated_at = await service.updated_at(user.id, repo)
    if updated_at is None:
        raise HTTPException(status_code=404, detail="Repo map not found")
    home = await endpoints.home(user.id, repo)
    if home is None:
        raise HTTPException(status_code=404, detail="Repo map not found")
    etag = ETag(home.model_dump(mode="json"))
    if etag.not_modified(request):
        return Response(status_code=304)
    etag.apply(response)
    return home


@router.get("/{repo:path}/flow", response_model=None)
async def get_repo_flow(
    repo: str,
    request: Request,
    response: Response,
    entry: str | None = None,
    helper: str | None = None,
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
    endpoints: EndpointViewService = Depends(get_endpoint_view_service),
) -> dict | Response:
    if entry and helper:
        raise HTTPException(status_code=400, detail="Provide either entry or helper, not both")
    view = await _flow_payload(repo, entry, helper, user, service, endpoints)
    etag = ETag(view)
    if etag.not_modified(request):
        return Response(status_code=304)
    etag.apply(response)
    return view


async def _flow_payload(
    repo: str,
    entry: str | None,
    helper: str | None,
    user: AuthUser,
    service: RepoMapService,
    endpoints: EndpointViewService,
) -> dict:
    if helper:
        view = await endpoints.helper_view(user.id, repo, helper)
        if view is None:
            raise HTTPException(status_code=404, detail="Helper not found")
        return view
    if entry:
        view = await endpoints.view(user.id, repo, entry)
        if view is None:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return view
    detail = await service.get(user.id, repo)
    if detail is None:
        raise HTTPException(status_code=404, detail="Repo map not found")
    flow_graph = detail.map.trace.get("flow_graph", {})
    return {
        "page_title": flow_graph.get("page_title", repo),
        "repo": repo,
        "repo_url": "",
        "view": detail.map.diagram.get("view", {}),
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

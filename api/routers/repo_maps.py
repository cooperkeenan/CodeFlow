from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_user, get_repo_map_service
from models.auth_model import AuthUser
from models.repo_map_model import RepoMapDetail, RepoMapListResponse
from services.repo_map_service import RepoMapService

router = APIRouter(prefix="/repomaps", tags=["repomaps"])


@router.get("", response_model=RepoMapListResponse)
async def list_repo_maps(
    user: AuthUser = Depends(get_current_user),
    service: RepoMapService = Depends(get_repo_map_service),
) -> RepoMapListResponse:
    return RepoMapListResponse(repo_maps=await service.list(user.id))


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

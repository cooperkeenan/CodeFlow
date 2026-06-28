from fastapi import APIRouter, Depends

from dependencies import get_github_service
from models.github_model import (
    GitHubCallbackRequest,
    GitHubCallbackResponse,
    RepositoriesResponse,
)
from services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/auth/callback", response_model=GitHubCallbackResponse)
async def github_callback(
    request: GitHubCallbackRequest,
    service: GitHubService = Depends(get_github_service),
) -> GitHubCallbackResponse:
    token = await service.exchange_code_for_token(request.code)
    return GitHubCallbackResponse(access_token=token)


@router.get("/repos", response_model=RepositoriesResponse)
async def list_repos(
    access_token: str,
    service: GitHubService = Depends(get_github_service),
) -> RepositoriesResponse:
    return await service.list_repositories(access_token)
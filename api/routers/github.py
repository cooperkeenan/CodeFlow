from fastapi import APIRouter, Depends

from dependencies import get_auth_service, get_github_service
from models.auth_model import SignInResponse
from models.github_model import (
    GitHubCallbackRequest,
    RepositoriesResponse,
)
from services.auth_service import AuthService
from services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/auth/callback", response_model=SignInResponse)
async def github_callback(
    request: GitHubCallbackRequest,
    service: AuthService = Depends(get_auth_service),
) -> SignInResponse:
    return await service.sign_in(request.code)


@router.get("/repos", response_model=RepositoriesResponse)
async def list_repos(
    access_token: str,
    service: GitHubService = Depends(get_github_service),
) -> RepositoriesResponse:
    return await service.list_repositories(access_token)
from fastapi import APIRouter, Depends
from gateway.deps import (
    get_auth_service,
    get_current_user,
    get_github_repo_service,
)
from gateway.models.auth_model import (
    AuthUser,
    GitHubCallbackRequest,
    RepositoriesResponse,
    SignInResponse,
)
from gateway.services.auth_service import AuthService
from gateway.services.github_repo_service import GitHubRepoService

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/auth/callback", response_model=SignInResponse)
async def github_callback(
    request: GitHubCallbackRequest,
    service: AuthService = Depends(get_auth_service),
) -> SignInResponse:
    return await service.sign_in(request.code)


@router.post("/link", response_model=AuthUser)
async def link_github(
    request: GitHubCallbackRequest,
    user: AuthUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> AuthUser:
    return await service.link_github(user, request.code)


@router.get("/my-repos", response_model=RepositoriesResponse)
async def list_my_repos(
    user: AuthUser = Depends(get_current_user),
    service: GitHubRepoService = Depends(get_github_repo_service),
) -> RepositoriesResponse:
    return await service.list_for_user(user.id)
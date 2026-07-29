from fastapi import HTTPException

from models.github_model import RepositoriesResponse
from services.github_service import GitHubService
from shared.user_store.user_store import UserStore


class GitHubRepoService:
    def __init__(self, user_store: UserStore, github_service: GitHubService) -> None:
        self._users = user_store
        self._github = github_service

    async def list_for_user(self, user_id: int) -> RepositoriesResponse:
        token = await self._users.get_github_token(user_id)
        if token is None:
            raise HTTPException(status_code=400, detail="GitHub not linked")
        return await self._github.list_repositories(token)

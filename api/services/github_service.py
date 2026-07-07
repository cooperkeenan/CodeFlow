from clients.github_client import GitHubClient
from models.github_model import RepositoriesResponse, RepositoryResponse


class GitHubService:
    def __init__(self, client: GitHubClient):
        self._client = client

    async def exchange_code_for_token(self, code: str) -> str:
        data = await self._client.exchange_code(code)
        return data["access_token"]

    async def get_identity(self, access_token: str) -> dict:
        user = await self._client.get_user(access_token)
        return {
            "id": user["id"],
            "login": user["login"],
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
        }

    async def list_repositories(self, access_token: str) -> RepositoriesResponse:
        repos = await self._client.list_repositories(access_token)
        return RepositoriesResponse(
            repositories=[
                RepositoryResponse(
                    name=r["name"],
                    full_name=r["full_name"],
                    owner=r["owner"]["login"],
                    description=r.get("description"),
                    url=r["html_url"],
                    language=r.get("language"),
                )
                for r in repos
            ]
        )
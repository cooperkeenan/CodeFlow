import httpx


class GitHubClient:
    _AUTH_URL = "https://github.com/login/oauth/access_token"
    _API_URL = "https://api.github.com"

    def __init__(self, http_client: httpx.AsyncClient, client_id: str, client_secret: str):
        self._http = http_client
        self._client_id = client_id
        self._client_secret = client_secret

    async def exchange_code(self, code: str) -> dict:
        response = await self._http.post(
            self._AUTH_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()

    async def list_repositories(self, access_token: str) -> list[dict]:
        response = await self._http.get(
            f"{self._API_URL}/user/repos",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            params={"per_page": 100, "sort": "updated"},
        )
        response.raise_for_status()
        return response.json()
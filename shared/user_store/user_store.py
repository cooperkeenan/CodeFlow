from typing import Protocol


class UserStore(Protocol):
    async def upsert(
        self, github_id: int, login: str, name: str | None, avatar_url: str | None
    ) -> int: ...

    async def create_with_password(self, email: str, password_hash: str) -> int: ...

    async def link_github(
        self,
        user_id: int,
        github_id: int,
        login: str,
        name: str | None,
        avatar_url: str | None,
    ) -> None: ...

    async def get(self, user_id: int) -> dict | None: ...

    async def get_by_email(self, email: str) -> dict | None: ...

    async def set_github_token(self, user_id: int, token: str) -> None: ...

    async def get_github_token(self, user_id: int) -> str | None: ...

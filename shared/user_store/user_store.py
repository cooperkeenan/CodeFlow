from typing import Protocol


class UserStore(Protocol):
    async def upsert(
        self, github_id: int, login: str, name: str | None, avatar_url: str | None
    ) -> int: ...

    async def get(self, user_id: int) -> dict | None: ...

from typing import Protocol


class DiagramEditStore(Protocol):
    async def get(self, user_id: int, repo: str) -> dict | None: ...

    async def upsert(self, user_id: int, repo: str, edits: dict) -> None: ...

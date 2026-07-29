from shared.diagram_edit_store.diagram_edit_store import DiagramEditStore


class DiagramEditService:
    def __init__(self, store: DiagramEditStore) -> None:
        self._store = store

    async def get(self, user_id: int, repo: str) -> dict:
        row = await self._store.get(user_id, repo)
        if row is None:
            return {}
        return row.get("edits", {})

    async def save(self, user_id: int, repo: str, edits: dict) -> None:
        await self._store.upsert(user_id, repo, edits)

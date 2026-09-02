from gateway.models.repo_map_model import AnalyseResponse, RepoMapDetail, RepoMapSummary

from shared.repo_map_store.repo_map_store import RepoMapStore


class RepoMapService:
    def __init__(self, repo_map_store: RepoMapStore) -> None:
        self._store = repo_map_store

    async def save(self, user_id: int, response: AnalyseResponse, source: str) -> None:
        await self._store.save(user_id, response.repo, source, response.model_dump(mode="json"))

    async def list(self, user_id: int) -> list[RepoMapSummary]:
        rows = await self._store.list_for_user(user_id)
        return [
            RepoMapSummary(
                repo=r["repo"],
                source=r["source"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    async def get(self, user_id: int, repo: str) -> RepoMapDetail | None:
        row = await self._store.get(user_id, repo)
        if row is None:
            return None
        return RepoMapDetail(
            repo=row["repo"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            map=AnalyseResponse.model_validate(row["payload"]),
        )

from shared.code_store.code_store import CodeStore


class CodeReadService:
    def __init__(self, code_store: CodeStore) -> None:
        self._code_store = code_store

    async def get_code(self, repo: str, file_path: str) -> dict | None:
        return await self._code_store.get_file(repo, file_path)

from typing import Protocol


class CodeStore(Protocol):
    async def put_file(self, repo: str, file_path: str, language: str, content: str) -> None: ...

    async def get_file(self, repo: str, file_path: str) -> dict | None: ...

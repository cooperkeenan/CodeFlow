import hashlib

from psycopg_pool import AsyncConnectionPool

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS code_files (
    repo         text,
    file_path    text,
    language     text,
    content      text,
    content_hash text,
    updated_at   timestamptz default now(),
    primary key (repo, file_path)
)
"""

_UPSERT = """
INSERT INTO code_files (repo, file_path, language, content, content_hash, updated_at)
VALUES (%s, %s, %s, %s, %s, now())
ON CONFLICT (repo, file_path) DO UPDATE
    SET language     = EXCLUDED.language,
        content      = EXCLUDED.content,
        content_hash = EXCLUDED.content_hash,
        updated_at   = now()
WHERE code_files.content_hash <> EXCLUDED.content_hash
"""

_SELECT = """
SELECT file_path, language, content
FROM code_files
WHERE repo = %s AND file_path = %s
"""


class NeonCodeStore:
    def __init__(self, database_url: str) -> None:
        self._pool: AsyncConnectionPool | None = None
        self._database_url = database_url

    async def _get_pool(self) -> AsyncConnectionPool:
        if self._pool is None:
            self._pool = AsyncConnectionPool(
                self._database_url,
                open=False,
                min_size=0,
                max_size=4,
                reconnect_timeout=30,
            )
            await self._pool.open()
            await self.ensure_schema()
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_CREATE_TABLE)

    async def put_file(self, repo: str, file_path: str, language: str, content: str) -> None:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_UPSERT, (repo, file_path, language, content, content_hash))

    async def get_file(self, repo: str, file_path: str) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_SELECT, (repo, file_path))
            row = await cursor.fetchone()
        if row is None:
            return None
        return {"file_path": row[0], "language": row[1], "content": row[2]}

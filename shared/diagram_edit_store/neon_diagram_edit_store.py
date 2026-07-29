from psycopg.types.json import Json
from psycopg_pool import AsyncConnectionPool

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS diagram_edits (
    id         bigserial primary key,
    user_id    bigint not null references users(id),
    repo       text not null,
    edits      jsonb not null default '{}',
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique (user_id, repo)
)
"""

_UPSERT = """
INSERT INTO diagram_edits (user_id, repo, edits, updated_at)
VALUES (%s, %s, %s, now())
ON CONFLICT (user_id, repo) DO UPDATE
    SET edits      = EXCLUDED.edits,
        updated_at = now()
"""

_SELECT = """
SELECT repo, edits, updated_at
FROM diagram_edits
WHERE user_id = %s AND repo = %s
"""


class NeonDiagramEditStore:
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
                check=AsyncConnectionPool.check_connection,
            )
            await self._pool.open()
            await self.ensure_schema()
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_CREATE_TABLE)

    async def upsert(self, user_id: int, repo: str, edits: dict) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_UPSERT, (user_id, repo, Json(edits)))

    async def get(self, user_id: int, repo: str) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_SELECT, (user_id, repo))
            row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "repo": row[0],
            "edits": row[1],
            "updated_at": row[2],
        }

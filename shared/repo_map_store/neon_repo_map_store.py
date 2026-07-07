from psycopg.types.json import Json
from psycopg_pool import AsyncConnectionPool

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS repo_maps (
    id         bigserial primary key,
    user_id    bigint not null references users(id),
    repo       text not null,
    source     text not null default 'web',
    payload    jsonb not null,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique (user_id, repo)
)
"""

_UPSERT = """
INSERT INTO repo_maps (user_id, repo, source, payload, updated_at)
VALUES (%s, %s, %s, %s, now())
ON CONFLICT (user_id, repo) DO UPDATE
    SET source     = EXCLUDED.source,
        payload    = EXCLUDED.payload,
        updated_at = now()
"""

_LIST = """
SELECT repo, source, created_at, updated_at
FROM repo_maps
WHERE user_id = %s
ORDER BY updated_at DESC
"""

_SELECT = """
SELECT repo, source, payload, created_at, updated_at
FROM repo_maps
WHERE user_id = %s AND repo = %s
"""


class NeonRepoMapStore:
    def __init__(self, database_url: str) -> None:
        self._pool: AsyncConnectionPool | None = None
        self._database_url = database_url

    async def _get_pool(self) -> AsyncConnectionPool:
        if self._pool is None:
            self._pool = AsyncConnectionPool(
                self._database_url,
                open=False,
                min_size=0,
                reconnect_timeout=30,
            )
            await self._pool.open()
            await self.ensure_schema()
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_CREATE_TABLE)

    async def save(self, user_id: int, repo: str, source: str, payload: dict) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_UPSERT, (user_id, repo, source, Json(payload)))

    async def list_for_user(self, user_id: int) -> list[dict]:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_LIST, (user_id,))
            rows = await cursor.fetchall()
        return [
            {"repo": r[0], "source": r[1], "created_at": r[2], "updated_at": r[3]}
            for r in rows
        ]

    async def get(self, user_id: int, repo: str) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_SELECT, (user_id, repo))
            row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "repo": row[0],
            "source": row[1],
            "payload": row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }

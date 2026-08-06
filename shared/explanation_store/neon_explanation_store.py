from psycopg.types.json import Json
from psycopg_pool import AsyncConnectionPool

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS explanations (
    fingerprint text primary key,
    repo        text not null,
    node_id     text not null,
    payload     jsonb not null,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
)
"""

_UPSERT = """
INSERT INTO explanations (fingerprint, repo, node_id, payload, updated_at)
VALUES (%s, %s, %s, %s, now())
ON CONFLICT (fingerprint) DO UPDATE
    SET payload    = EXCLUDED.payload,
        updated_at = now()
"""

_SELECT = """
SELECT payload
FROM explanations
WHERE fingerprint = %s
"""


class NeonExplanationStore:
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

    async def put(self, fingerprint: str, repo: str, node_id: str, payload: dict) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_UPSERT, (fingerprint, repo, node_id, Json(payload)))

    async def get(self, fingerprint: str) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_SELECT, (fingerprint,))
            row = await cursor.fetchone()
        if row is None:
            return None
        return row[0]

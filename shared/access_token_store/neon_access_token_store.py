from psycopg_pool import AsyncConnectionPool

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS access_tokens (
    id           bigserial primary key,
    user_id      bigint not null references users(id),
    kind         text not null,
    name         text,
    token_hash   text unique not null,
    token_prefix text not null,
    created_at   timestamptz default now(),
    last_used_at timestamptz,
    revoked_at   timestamptz
)
"""

_INSERT = """
INSERT INTO access_tokens (user_id, kind, name, token_hash, token_prefix)
VALUES (%s, %s, %s, %s, %s)
RETURNING id
"""

_SELECT_BY_HASH = """
SELECT id, user_id, kind, name, token_prefix, revoked_at
FROM access_tokens
WHERE token_hash = %s
"""

_LIST = """
SELECT id, name, token_prefix, created_at, last_used_at, revoked_at
FROM access_tokens
WHERE user_id = %s AND kind = %s
ORDER BY created_at DESC
"""

_REVOKE = """
UPDATE access_tokens
SET revoked_at = now()
WHERE id = %s AND user_id = %s AND revoked_at IS NULL
"""

_TOUCH = "UPDATE access_tokens SET last_used_at = now() WHERE id = %s"


class NeonAccessTokenStore:
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

    async def create(
        self, user_id: int, kind: str, name: str | None, token_hash: str, prefix: str
    ) -> int:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_INSERT, (user_id, kind, name, token_hash, prefix))
            row = await cursor.fetchone()
        assert row is not None
        return row[0]

    async def get_by_hash(self, token_hash: str) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_SELECT_BY_HASH, (token_hash,))
            row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "user_id": row[1],
            "kind": row[2],
            "name": row[3],
            "token_prefix": row[4],
            "revoked_at": row[5],
        }

    async def list_for_user(self, user_id: int, kind: str) -> list[dict]:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_LIST, (user_id, kind))
            rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "token_prefix": r[2],
                "created_at": r[3],
                "last_used_at": r[4],
                "revoked_at": r[5],
            }
            for r in rows
        ]

    async def revoke(self, user_id: int, token_id: int) -> bool:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_REVOKE, (token_id, user_id))
        return cursor.rowcount > 0

    async def touch_last_used(self, token_id: int) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(_TOUCH, (token_id,))

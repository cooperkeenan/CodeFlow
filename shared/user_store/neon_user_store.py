from psycopg_pool import AsyncConnectionPool

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id           bigserial primary key,
    github_id    bigint unique not null,
    github_login text not null,
    name         text,
    avatar_url   text,
    created_at   timestamptz default now(),
    updated_at   timestamptz default now()
)
"""

_UPSERT = """
INSERT INTO users (github_id, github_login, name, avatar_url, updated_at)
VALUES (%s, %s, %s, %s, now())
ON CONFLICT (github_id) DO UPDATE
    SET github_login = EXCLUDED.github_login,
        name         = EXCLUDED.name,
        avatar_url   = EXCLUDED.avatar_url,
        updated_at   = now()
RETURNING id
"""

_SELECT = """
SELECT id, github_id, github_login, name, avatar_url
FROM users
WHERE id = %s
"""


class NeonUserStore:
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

    async def upsert(
        self, github_id: int, login: str, name: str | None, avatar_url: str | None
    ) -> int:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_UPSERT, (github_id, login, name, avatar_url))
            row = await cursor.fetchone()
        return row[0]

    async def get(self, user_id: int) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(_SELECT, (user_id,))
            row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "github_id": row[1],
            "github_login": row[2],
            "name": row[3],
            "avatar_url": row[4],
        }

from psycopg_pool import AsyncConnectionPool

from shared.user_store import _user_queries as q


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
            await conn.execute(q.CREATE_TABLE)
            for migration in q.MIGRATIONS:
                await conn.execute(migration)

    async def upsert(
        self, github_id: int, login: str, name: str | None, avatar_url: str | None
    ) -> int:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(q.UPSERT, (github_id, login, name, avatar_url))
            row = await cursor.fetchone()
        assert row is not None
        return row[0]

    async def create_with_password(self, email: str, password_hash: str) -> int:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(q.CREATE_WITH_PASSWORD, (email, password_hash))
            row = await cursor.fetchone()
        assert row is not None
        return row[0]

    async def link_github(
        self,
        user_id: int,
        github_id: int,
        login: str,
        name: str | None,
        avatar_url: str | None,
    ) -> None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(q.LINK_GITHUB, (github_id, login, name, avatar_url, user_id))

    async def get(self, user_id: int) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(q.SELECT, (user_id,))
            row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "github_id": row[1],
            "github_login": row[2],
            "name": row[3],
            "avatar_url": row[4],
            "email": row[5],
        }

    async def get_by_email(self, email: str) -> dict | None:
        pool = await self._get_pool()
        async with pool.connection() as conn:
            cursor = await conn.execute(q.SELECT_BY_EMAIL, (email,))
            row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "github_id": row[1],
            "github_login": row[2],
            "name": row[3],
            "avatar_url": row[4],
            "email": row[5],
            "password_hash": row[6],
        }

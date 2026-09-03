import psycopg

_SELECT_BY_HANDLE = """
SELECT id FROM users
WHERE lower(github_login) = lower(%s) OR lower(email) = lower(%s)
"""


class UserHandleResolver:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def resolve(self, handle: str) -> int:
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(_SELECT_BY_HANDLE, (handle, handle))
                row = cursor.fetchone()
        if row is None:
            raise ValueError(f"no user found for handle '{handle}'")
        return row[0]

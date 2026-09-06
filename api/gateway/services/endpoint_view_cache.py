from datetime import datetime

from shared.caching.lru_cache import LruCache

_DEFAULT_MAXSIZE = 200


class EndpointViewCache:
    def __init__(self, cache: LruCache[dict] | None = None) -> None:
        self._cache = cache if cache is not None else LruCache[dict](_DEFAULT_MAXSIZE)

    def get(self, user_id: int, repo: str, updated_at: datetime, view_key: str) -> dict | None:
        return self._cache.get((user_id, repo, updated_at, view_key))

    def put(
        self,
        user_id: int,
        repo: str,
        updated_at: datetime,
        view_key: str,
        value: dict,
    ) -> None:
        self._cache.put((user_id, repo, updated_at, view_key), value)

from datetime import datetime

from shared.caching.lru_cache import LruCache
from shared.models.flow_graph import FlowGraph

_DEFAULT_MAXSIZE = 8


class FlowGraphCache:
    def __init__(self, cache: LruCache[FlowGraph] | None = None) -> None:
        self._cache = cache if cache is not None else LruCache[FlowGraph](_DEFAULT_MAXSIZE)

    def get(self, user_id: int, repo: str, updated_at: datetime) -> FlowGraph | None:
        return self._cache.get((user_id, repo, updated_at))

    def put(self, user_id: int, repo: str, updated_at: datetime, graph: FlowGraph) -> None:
        self._cache.put((user_id, repo, updated_at), graph)

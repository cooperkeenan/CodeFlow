from collections import OrderedDict
from typing import Generic, TypeVar

T = TypeVar("T")


class LruCache(Generic[T]):
    def __init__(self, maxsize: int) -> None:
        self._maxsize = maxsize
        self._entries: OrderedDict[tuple[object, ...], T] = OrderedDict()

    def get(self, key: tuple[object, ...]) -> T | None:
        if key not in self._entries:
            return None
        self._entries.move_to_end(key)
        return self._entries[key]

    def put(self, key: tuple[object, ...], value: T) -> None:
        self._entries[key] = value
        self._entries.move_to_end(key)
        while len(self._entries) > self._maxsize:
            self._entries.popitem(last=False)

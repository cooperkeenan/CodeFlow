import json
from collections.abc import Callable
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


class JsonCache(Generic[T]):
    def __init__(
        self,
        path: Path,
        serialize: Callable[[T], dict],
        deserialize: Callable[[dict], T],
    ) -> None:
        self._path = path
        self._serialize = serialize
        self._deserialize = deserialize
        self._entries: dict[str, T] = self._load()

    def get(self, fingerprint: str) -> T | None:
        return self._entries.get(fingerprint)

    def put(self, fingerprint: str, value: T) -> None:
        self._entries[fingerprint] = value

    def flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: self._serialize(value) for key, value in self._entries.items()}
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _load(self) -> dict[str, T]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        entries: dict[str, T] = {}
        for key, value in raw.items():
            try:
                entries[key] = self._deserialize(value)
            except (KeyError, TypeError, ValueError):
                continue
        return entries

import json
from pathlib import Path

from tracer.models.naming import NodeNaming


class NameCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, NodeNaming] = self._load()

    def get(self, fingerprint: str) -> NodeNaming | None:
        return self._entries.get(fingerprint)

    def put(self, fingerprint: str, naming: NodeNaming) -> None:
        self._entries[fingerprint] = naming

    def flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: self._serialize(value) for key, value in self._entries.items()}
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    def _load(self) -> dict[str, NodeNaming]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        entries: dict[str, NodeNaming] = {}
        for key, value in raw.items():
            try:
                entries[key] = self._deserialize(value)
            except (KeyError, TypeError, ValueError):
                continue
        return entries

    def _serialize(self, naming: NodeNaming) -> dict:
        return {"label": naming.label, "one_liner": naming.one_liner}

    def _deserialize(self, value: dict) -> NodeNaming:
        return NodeNaming(label=value["label"], one_liner=value["one_liner"])

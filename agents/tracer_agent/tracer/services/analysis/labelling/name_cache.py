from pathlib import Path

from tracer.models.naming import NodeNaming
from tracer.services.analysis.json_cache import JsonCache


def _serialize(naming: NodeNaming) -> dict:
    return {"label": naming.label, "one_liner": naming.one_liner}


def _deserialize(value: dict) -> NodeNaming:
    return NodeNaming(label=value["label"], one_liner=value["one_liner"])


class NameCache(JsonCache[NodeNaming]):
    def __init__(self, path: Path) -> None:
        super().__init__(path, _serialize, _deserialize)

import json
from pathlib import Path

from pydantic import BaseModel


class OutputPersister:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir

    def write_json(self, name: str, payload) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, BaseModel):
            content = payload.model_dump_json(indent=2)
        else:
            content = json.dumps(payload, indent=2)
        (self._base_dir / name).write_text(content)

    def write_text(self, name: str, content: str) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        (self._base_dir / name).write_text(content)

import json
from pathlib import Path

from tracer.models.verdicts import StitchVerdict


class StitchVerdictCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, StitchVerdict] = self._load()

    def get(self, fingerprint: str) -> StitchVerdict | None:
        return self._entries.get(fingerprint)

    def put(self, fingerprint: str, verdict: StitchVerdict) -> None:
        self._entries[fingerprint] = verdict

    def flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: self._serialize(value) for key, value in self._entries.items()}
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    def _load(self) -> dict[str, StitchVerdict]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        entries: dict[str, StitchVerdict] = {}
        for key, value in raw.items():
            try:
                entries[key] = self._deserialize(value)
            except (KeyError, TypeError, ValueError):
                continue
        return entries

    def _serialize(self, verdict: StitchVerdict) -> dict:
        return {"target_id": verdict.target_id, "confidence": verdict.confidence}

    def _deserialize(self, value: dict) -> StitchVerdict:
        return StitchVerdict(target_id=value.get("target_id"), confidence=value["confidence"])

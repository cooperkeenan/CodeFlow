import json
from pathlib import Path

from tracer.models.verdicts import DecisionVerdict


class VerdictCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, DecisionVerdict] = self._load()

    def get(self, fingerprint: str) -> DecisionVerdict | None:
        return self._entries.get(fingerprint)

    def put(self, fingerprint: str, verdict: DecisionVerdict) -> None:
        self._entries[fingerprint] = verdict

    def flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: self._serialize(value) for key, value in self._entries.items()}
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    def _load(self) -> dict[str, DecisionVerdict]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        entries: dict[str, DecisionVerdict] = {}
        for key, value in raw.items():
            try:
                entries[key] = self._deserialize(value)
            except (KeyError, TypeError, ValueError):
                continue
        return entries

    def _serialize(self, verdict: DecisionVerdict) -> dict:
        return {
            "verdict": verdict.verdict,
            "question": verdict.question,
            "arm_labels": list(verdict.arm_labels),
            "confidence": verdict.confidence,
            "importance": verdict.importance,
        }

    def _deserialize(self, value: dict) -> DecisionVerdict:
        return DecisionVerdict(
            verdict=value["verdict"],
            question=value["question"],
            arm_labels=tuple(value["arm_labels"]),
            confidence=value["confidence"],
            importance=value.get("importance", 0.0),
        )

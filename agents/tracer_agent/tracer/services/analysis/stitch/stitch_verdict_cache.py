from pathlib import Path

from tracer.models.verdicts import StitchVerdict
from tracer.services.analysis.json_cache import JsonCache


def _serialize(verdict: StitchVerdict) -> dict:
    return {"target_id": verdict.target_id, "confidence": verdict.confidence}


def _deserialize(value: dict) -> StitchVerdict:
    return StitchVerdict(target_id=value.get("target_id"), confidence=value["confidence"])


class StitchVerdictCache(JsonCache[StitchVerdict]):
    def __init__(self, path: Path) -> None:
        super().__init__(path, _serialize, _deserialize)

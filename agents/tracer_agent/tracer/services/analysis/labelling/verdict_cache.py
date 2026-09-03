from pathlib import Path

from tracer.models.verdicts import DecisionVerdict
from tracer.services.analysis.json_cache import JsonCache


def _serialize(verdict: DecisionVerdict) -> dict:
    return {
        "verdict": verdict.verdict,
        "question": verdict.question,
        "arm_labels": list(verdict.arm_labels),
        "confidence": verdict.confidence,
        "importance": verdict.importance,
    }


def _deserialize(value: dict) -> DecisionVerdict:
    return DecisionVerdict(
        verdict=value["verdict"],
        question=value["question"],
        arm_labels=tuple(value["arm_labels"]),
        confidence=value["confidence"],
        importance=value.get("importance", 0.0),
    )


class VerdictCache(JsonCache[DecisionVerdict]):
    def __init__(self, path: Path) -> None:
        super().__init__(path, _serialize, _deserialize)

from dataclasses import dataclass


@dataclass(frozen=True)
class StitchVerdict:
    target_id: str | None
    confidence: float

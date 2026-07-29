from dataclasses import dataclass

from models.site_verdict import Verdict


@dataclass(frozen=True)
class DecisionVerdict:
    verdict: Verdict
    question: str
    arm_labels: tuple[str, ...]
    confidence: float

from dataclasses import dataclass
from typing import Literal

Verdict = Literal["decision", "guarded_step", "noise"]
ArmClass = Literal["void", "guard", "live"]


@dataclass(frozen=True)
class SiteVerdict:
    site_id: str
    verdict: Verdict
    score: float
    arm_reach_sizes: tuple[int, ...]
    arm_classes: tuple[ArmClass, ...]
    question: str = ""
    arm_labels: tuple[str, ...] = ()

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from tracer.models.sites import DispatchSite

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
    importance: float = 0.0


@dataclass(frozen=True)
class DecisionCandidate:
    site_id: str
    site: DispatchSite
    arm_classes: tuple[ArmClass, ...]
    arm_reach_sizes: tuple[int, ...]
    arm_reaches: tuple[frozenset[str], ...]
    heuristic_score: float
    source_snippet: str


@dataclass(frozen=True)
class DecisionVerdict:
    verdict: Verdict
    question: str
    arm_labels: tuple[str, ...]
    confidence: float
    importance: float


@dataclass(frozen=True)
class SignificanceResult:
    utilities: frozenset[str]
    verdicts: Mapping[str, SiteVerdict]
    ranked_decisions: tuple[str, ...]


@dataclass(frozen=True)
class StitchVerdict:
    target_id: str | None
    confidence: float

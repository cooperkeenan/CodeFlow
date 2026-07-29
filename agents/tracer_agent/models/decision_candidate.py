from dataclasses import dataclass

from models.dispatch_site import DispatchSite
from models.site_verdict import ArmClass


@dataclass(frozen=True)
class DecisionCandidate:
    site_id: str
    site: DispatchSite
    arm_classes: tuple[ArmClass, ...]
    arm_reach_sizes: tuple[int, ...]
    arm_reaches: tuple[frozenset[str], ...]
    heuristic_score: float
    source_snippet: str

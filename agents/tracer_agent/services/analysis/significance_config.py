from dataclasses import dataclass


@dataclass(frozen=True)
class SignificanceConfig:
    utility_min_fan_in: int = 8
    utility_percentile: float = 0.90
    reach_max_depth: int = 6
    guard_reach_limit: int = 2
    weight_reach: float = 3.0
    weight_provenance: float = 2.0
    weight_terminal: float = 2.0
    weight_dispatch_kind: float = 1.0
    pillar_hits_iterations: int = 50
    pillar_score_decimals: int = 6

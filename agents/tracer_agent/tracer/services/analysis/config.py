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


@dataclass(frozen=True)
class BudgetConfig:
    node_budget: int = 40
    max_arms_per_decision: int = 5
    min_lane_nodes: int = 3
    visible_decisions: int = 8
    skeleton_budget: int = 15
    max_reveal_per_node: int = 8
    seed_anchors_per_lane: int = 3
    max_body: int = 6

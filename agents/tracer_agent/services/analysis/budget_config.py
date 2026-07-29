from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetConfig:
    node_budget: int = 36
    max_arms_per_decision: int = 5
    min_lane_nodes: int = 3

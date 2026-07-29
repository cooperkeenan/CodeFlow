from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetConfig:
    node_budget: int = 40
    max_arms_per_decision: int = 5
    min_lane_nodes: int = 3
    visible_decisions: int = 8

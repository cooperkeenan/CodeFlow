from dataclasses import dataclass


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

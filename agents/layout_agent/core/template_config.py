from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateLimitsConfig:
    pipeline: int = 8
    hub_and_spoke: int = 8
    layered_tier: int = 10
    hierarchy: int = 10
    hierarchy_max_depth: int = 3
    mesh: int = 12
    dependency_graph: int = 10

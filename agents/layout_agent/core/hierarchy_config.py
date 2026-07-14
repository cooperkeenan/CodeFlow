from dataclasses import dataclass


@dataclass(frozen=True)
class HierarchyConfig:
    architecture_node_cap: int = 8
    service_max_components: int = 12
    service_max_steps: int = 8
    min_group_children: int = 2

from dataclasses import dataclass

from shared.models.flow_graph import FlowNode


@dataclass(frozen=True)
class NodeNameContext:
    node: FlowNode
    arm_label_sources: tuple[str, ...]
    child_labels: tuple[str, ...]
